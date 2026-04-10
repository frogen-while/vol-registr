"""Schedule / Match CRUD, CSV import, quick panel, conflict detection."""

from collections import OrderedDict

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from ..admin_forms import AdminMatchForm, AdminScheduleEventForm
from ..constants import (
    COURT_CHOICES,
    EVENT_TYPE_CHOICES,
    MATCH_FINISHED,
    MATCH_LIVE,
    MATCH_SCHEDULED,
    MATCH_STATUS_CHOICES,
    STAGE_CHOICES,
)
from ..models import AUDIT_CATEGORY_MATCH, Match, ScheduleEvent
from .audit import log_audit


@staff_member_required(login_url="/panel/login/")
def schedule_list_view(request):
    qs = Match.objects.select_related("team_a", "team_b")

    # ── Filters ──
    stage = request.GET.get("stage", "")
    status = request.GET.get("status", "")
    court = request.GET.get("court", "")
    group = request.GET.get("group", "")

    if stage:
        qs = qs.filter(stage=stage)
    if status:
        qs = qs.filter(status=status)
    if court:
        qs = qs.filter(court=court)
    if group:
        qs = qs.filter(group=group)

    qs = qs.order_by("start_time", "court")

    # View mode: table (default) or grid
    view_mode = request.GET.get("view", "table")

    # ── Detect conflicts across all matches ──
    all_matches = list(qs)
    conflict_pks = set()
    # Build lookup for double-booking detection
    time_court = {}   # (start_time, court) → [match]
    time_team = {}    # (start_time, team_id) → [match]
    for m in all_matches:
        key_ct = (m.start_time, m.court)
        time_court.setdefault(key_ct, []).append(m)
        if m.team_a_id:
            time_team.setdefault((m.start_time, m.team_a_id), []).append(m)
        if m.team_b_id:
            time_team.setdefault((m.start_time, m.team_b_id), []).append(m)
    for key, matches in time_court.items():
        if len(matches) > 1:
            for m in matches:
                conflict_pks.add(m.pk)
    for key, matches in time_team.items():
        if len(matches) > 1:
            for m in matches:
                conflict_pks.add(m.pk)

    # Build grid data: rows=timeslots, cols=courts
    grid_data = []
    if view_mode == "grid":
        slots = OrderedDict()
        for m in qs:
            slot_key = m.start_time
            slots.setdefault(slot_key, {})
            slots[slot_key][m.court] = m
        courts = [c[0] for c in COURT_CHOICES]
        for slot_time, court_map in slots.items():
            grid_data.append({
                "time": slot_time,
                "cells": [court_map.get(c) for c in courts],
            })

    # Groups for filter dropdown
    groups = (
        Match.objects.exclude(group="")
        .values_list("group", flat=True)
        .distinct()
        .order_by("group")
    )

    ctx = {
        "page_title": "Schedule",
        "nav_section": "schedule",
        "matches": qs,
        "events": ScheduleEvent.objects.all(),
        "stage_filter": stage,
        "status_filter": status,
        "court_filter": court,
        "group_filter": group,
        "view_mode": view_mode,
        "grid_data": grid_data,
        "courts": COURT_CHOICES,
        "stage_choices": STAGE_CHOICES,
        "match_status_choices": MATCH_STATUS_CHOICES,
        "event_type_choices": EVENT_TYPE_CHOICES,
        "groups": groups,
        "conflict_pks": conflict_pks,
    }
    return render(request, "panel/schedule_list.html", ctx)


@staff_member_required(login_url="/panel/login/")
def match_create_view(request):
    if request.method == "POST":
        form = AdminMatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            messages.success(request, f"Match #{match.match_number} created.")
            return redirect("panel:schedule")
    else:
        form = AdminMatchForm()
    return render(
        request,
        "panel/match_form.html",
        {"page_title": "Create Match", "nav_section": "schedule", "form": form},
    )


@staff_member_required(login_url="/panel/login/")
def match_edit_view(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.method == "POST":
        form = AdminMatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, f"Match #{match.match_number} updated.")
            return redirect("panel:schedule")
    else:
        form = AdminMatchForm(instance=match)
    return render(
        request,
        "panel/match_form.html",
        {"page_title": f"Edit Match #{match.match_number}", "nav_section": "schedule", "form": form, "match": match},
    )


@staff_member_required(login_url="/panel/login/")
@require_POST
def match_delete_view(request, pk):
    match = get_object_or_404(Match, pk=pk)
    num = match.match_number
    match.delete()
    messages.success(request, f"Match #{num} deleted.")
    return redirect("panel:schedule")


@staff_member_required(login_url="/panel/login/")
def schedule_csv_import_view(request):
    from ..services import import_schedule_csv, parse_schedule_csv

    preview = None
    csv_errors = []
    confirmed = False

    if request.method == "POST":
        if "confirm" in request.POST:
            # ── Step 2: Confirm import ──
            cached = request.session.pop("_schedule_csv_rows", None)
            if not cached:
                messages.error(request, "Session expired. Please upload the file again.")
            else:
                from datetime import datetime

                for r in cached:
                    r["time"] = datetime.fromisoformat(r["time"])
                count = import_schedule_csv(cached)
                messages.success(request, f"{count} match(es) imported.")
                confirmed = True
                return redirect("panel:schedule")
        else:
            # ── Step 1: Upload + parse ──
            csv_file = request.FILES.get("csv_file")
            if not csv_file:
                messages.error(request, "Please select a CSV file.")
            else:
                result = parse_schedule_csv(csv_file)
                csv_errors = result["errors"]
                if not csv_errors and result["rows"]:
                    preview = result["rows"]
                    # Cache rows in session for confirm step
                    session_rows = []
                    for r in result["rows"]:
                        session_rows.append({
                            **r,
                            "time": r["time"].isoformat(),
                        })
                    request.session["_schedule_csv_rows"] = session_rows
                elif not csv_errors and not result["rows"]:
                    csv_errors = ["No valid rows found in CSV."]

    return render(request, "panel/schedule_csv_import.html", {
        "page_title": "Import Schedule CSV",
        "nav_section": "schedule",
        "preview": preview,
        "csv_errors": csv_errors,
    })


# ── Match status transitions ────────────────────────────

_MATCH_TRANSITIONS = {
    MATCH_SCHEDULED: [MATCH_LIVE],
    MATCH_LIVE: [MATCH_FINISHED, MATCH_SCHEDULED],
    MATCH_FINISHED: [MATCH_LIVE],
}


# ── Match quick panel (AJAX drawer) ─────────────────────

@staff_member_required(login_url="/panel/login/")
def match_panel_view(request, pk):
    """AJAX — render match quick panel partial, return JSON with html."""
    match = get_object_or_404(
        Match.objects.select_related("team_a", "team_b"), pk=pk
    )
    transitions = _MATCH_TRANSITIONS.get(match.status, [])
    transition_labels = dict(MATCH_STATUS_CHOICES)
    html = render_to_string("panel/partials/match_panel.html", {
        "m": match,
        "transitions": [(s, transition_labels.get(s, s)) for s in transitions],
    }, request=request)
    return JsonResponse({"html": html})


@staff_member_required(login_url="/panel/login/")
@require_POST
def match_status_change(request, pk):
    """AJAX — change match status. Returns JSON."""
    match = get_object_or_404(Match, pk=pk)
    new_status = request.POST.get("new_status", "")
    allowed = _MATCH_TRANSITIONS.get(match.status, [])
    if new_status not in allowed:
        return JsonResponse(
            {"ok": False, "error": f"Cannot move from {match.status} to {new_status}"},
            status=400,
        )
    match.status = new_status
    match.save(update_fields=["status"])
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_MATCH,
        action=f"Status → {match.get_status_display()}",
        entity_type="Match", entity_id=match.pk,
        entity_label=f"M{match.match_number}",
    )
    return JsonResponse({
        "ok": True,
        "new_status": match.status,
        "new_label": match.get_status_display(),
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def match_score_update(request, pk):
    """AJAX — quick score update from the panel. Returns JSON."""
    match = get_object_or_404(Match, pk=pk)
    try:
        score_a = int(request.POST.get("score_a", match.score_a))
        score_b = int(request.POST.get("score_b", match.score_b))
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "Invalid score"}, status=400)
    match.score_a = score_a
    match.score_b = score_b
    match.save(update_fields=["score_a", "score_b"])
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_MATCH,
        action=f"Score updated: {score_a}-{score_b}",
        entity_type="Match", entity_id=match.pk,
        entity_label=f"M{match.match_number}",
    )
    return JsonResponse({"ok": True, "score_a": match.score_a, "score_b": match.score_b})


# ── Conflict check endpoint ─────────────────────────────

@staff_member_required(login_url="/panel/login/")
def match_conflict_check(request):
    """AJAX GET — check for conflicts on a court/time/teams. Returns JSON."""
    court = request.GET.get("court", "")
    start_time = request.GET.get("start_time", "")
    team_a_id = request.GET.get("team_a", "")
    team_b_id = request.GET.get("team_b", "")
    exclude_pk = request.GET.get("exclude", "")

    conflicts = []
    qs = Match.objects.select_related("team_a", "team_b")
    if exclude_pk:
        qs = qs.exclude(pk=int(exclude_pk))

    # Court/time conflict
    if court and start_time:
        court_matches = qs.filter(court=int(court), start_time=start_time)
        for m in court_matches:
            conflicts.append({
                "type": "court",
                "message": f"Court {court} already booked: Match #{m.match_number} ({m.team_a or 'TBD'} vs {m.team_b or 'TBD'})",
            })

    # Team double-booking
    if start_time:
        for tid, label in [(team_a_id, "Team A"), (team_b_id, "Team B")]:
            if not tid:
                continue
            from django.db.models import Q
            team_matches = qs.filter(
                Q(team_a_id=int(tid)) | Q(team_b_id=int(tid)),
                start_time=start_time,
            )
            for m in team_matches:
                team_name = m.team_a.name if m.team_a_id == int(tid) else (m.team_b.name if m.team_b else "TBD")
                conflicts.append({
                    "type": "team",
                    "message": f"{label} ({team_name}) already playing: Match #{m.match_number} at the same time",
                })

    return JsonResponse({"conflicts": conflicts})


# ── Schedule Events CRUD ─────────────────────────────────

@staff_member_required(login_url="/panel/login/")
def event_create_view(request):
    if request.method == "POST":
        form = AdminScheduleEventForm(request.POST)
        if form.is_valid():
            event = form.save()
            messages.success(request, f"Event '{event.title}' created.")
            return redirect("panel:schedule")
    else:
        form = AdminScheduleEventForm()
    return render(
        request,
        "panel/event_form.html",
        {"page_title": "Create Event", "nav_section": "schedule", "form": form},
    )


@staff_member_required(login_url="/panel/login/")
def event_edit_view(request, pk):
    event = get_object_or_404(ScheduleEvent, pk=pk)
    if request.method == "POST":
        form = AdminScheduleEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f"Event '{event.title}' updated.")
            return redirect("panel:schedule")
    else:
        form = AdminScheduleEventForm(instance=event)
    return render(
        request,
        "panel/event_form.html",
        {"page_title": f"Edit Event: {event.title}", "nav_section": "schedule", "form": form, "event": event},
    )


@staff_member_required(login_url="/panel/login/")
@require_POST
def event_delete_view(request, pk):
    event = get_object_or_404(ScheduleEvent, pk=pk)
    title = event.title
    event.delete()
    messages.success(request, f"Event '{title}' deleted.")
    return redirect("panel:schedule")
