"""Custom admin panel views — all protected by @staff_member_required."""

import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .admin_forms import (
    AdminMatchForm,
    AdminTeamForm,
    GalleryBulkForm,
    GalleryPhotoForm,
    GalleryVideoForm,
    PlayerInlineFormSet,
    _drive_thumbnail,
    _drive_view_url,
    _parse_drive_file_id,
)
from .constants import (
    COURT_CHOICES,
    MATCH_FINISHED,
    MATCH_SCHEDULED,
    MATCH_STATUS_CHOICES,
    PAYMENT_STATUS_CHOICES,
    POSITION_CHOICES,
    STAGE_CHOICES,
    STAGE_GROUP,
    TEAM_STATUS_APPROVED,
    TEAM_STATUS_AWAITING_PAYMENT,
    TEAM_STATUS_CHOICES,
    TEAM_STATUS_PAID,
    TEAM_STATUS_REGISTERED,
)
from .models import DreamTeamEntry, GalleryPhoto, GalleryVideo, Match, Player, PlayerMatchStats, Team, TeamMatchStats

# Allowed status transitions: current → list of valid next statuses
_STATUS_TRANSITIONS = {
    TEAM_STATUS_REGISTERED: [TEAM_STATUS_AWAITING_PAYMENT],
    TEAM_STATUS_AWAITING_PAYMENT: [TEAM_STATUS_PAID, TEAM_STATUS_REGISTERED],
    TEAM_STATUS_PAID: [TEAM_STATUS_APPROVED, TEAM_STATUS_AWAITING_PAYMENT],
    TEAM_STATUS_APPROVED: [TEAM_STATUS_PAID],
}


# ── Auth ─────────────────────────────────────────────────


def panel_login(request):
    """Staff login page for the custom panel."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("panel:dashboard")

    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.GET.get("next", "panel:dashboard")
            return redirect(next_url)
        error = "Invalid credentials or insufficient permissions."

    return render(request, "panel/login.html", {"error": error})


def panel_logout(request):
    """Log out and redirect to panel login."""
    logout(request)
    return redirect("panel:login")


# ── Dashboard ────────────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def dashboard_view(request):
    now = timezone.now()

    teams_total = Team.objects.count()
    teams_by_status = dict(
        Team.objects.values_list("status").annotate(c=Count("id")).values_list("status", "c")
    )
    players_total = Player.objects.count()
    checkin_count = Team.objects.filter(checked_in=True).count()

    matches_total = Match.objects.count()
    matches_finished = Match.objects.filter(status=MATCH_FINISHED).count()
    matches_remaining = matches_total - matches_finished

    gallery_count = GalleryPhoto.objects.count()

    recent_teams = Team.objects.order_by("-created_at")[:5]
    upcoming_matches = (
        Match.objects.filter(status=MATCH_SCHEDULED, start_time__gte=now)
        .select_related("team_a", "team_b")
        .order_by("start_time")[:5]
    )

    ctx = {
        "page_title": "Dashboard",
        "nav_section": "dashboard",
        "teams_total": teams_total,
        "teams_by_status": teams_by_status,
        "players_total": players_total,
        "checkin_count": checkin_count,
        "checkin_of": Team.objects.filter(status=TEAM_STATUS_APPROVED).count(),
        "matches_total": matches_total,
        "matches_finished": matches_finished,
        "matches_remaining": matches_remaining,
        "gallery_count": gallery_count,
        "recent_teams": recent_teams,
        "upcoming_matches": upcoming_matches,
    }
    return render(request, "panel/dashboard.html", ctx)


# ── Teams ────────────────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def teams_list_view(request):
    qs = Team.objects.annotate(player_count=Count("players"))

    # ── Filters ──
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    payment = request.GET.get("payment", "")
    group = request.GET.get("group", "")
    checkin = request.GET.get("checkin", "")

    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(cap_name__icontains=q)
            | Q(cap_surname__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if payment != "":
        qs = qs.filter(payment_status=payment)
    if group:
        qs = qs.filter(group_name=group)
    if checkin == "1":
        qs = qs.filter(checked_in=True)
    elif checkin == "0":
        qs = qs.filter(checked_in=False)

    # ── Sorting ──
    sort = request.GET.get("sort", "name")
    direction = request.GET.get("dir", "asc")
    allowed_sorts = {
        "name": "name",
        "group": "group_name",
        "status": "status",
        "payment": "payment_status",
        "players": "player_count",
        "created": "created_at",
    }
    order_field = allowed_sorts.get(sort, "name")
    if direction == "desc":
        order_field = f"-{order_field}"
    qs = qs.order_by(order_field)

    groups = (
        Team.objects.exclude(group_name__isnull=True)
        .exclude(group_name="")
        .values_list("group_name", flat=True)
        .distinct()
        .order_by("group_name")
    )

    ctx = {
        "page_title": "Teams",
        "nav_section": "teams",
        "teams": qs,
        "q": q,
        "status": status,
        "payment": payment,
        "group": group,
        "checkin": checkin,
        "sort": request.GET.get("sort", "name"),
        "dir": direction,
        "status_choices": TEAM_STATUS_CHOICES,
        "payment_choices": PAYMENT_STATUS_CHOICES,
        "groups": groups,
    }
    return render(request, "panel/teams_list.html", ctx)


@staff_member_required(login_url="/panel/login/")
def team_detail_view(request, pk):
    team = get_object_or_404(Team.objects.prefetch_related("players"), pk=pk)
    team_matches = (
        Match.objects.filter(Q(team_a=team) | Q(team_b=team))
        .select_related("team_a", "team_b")
        .order_by("-start_time")
    )
    next_statuses = _STATUS_TRANSITIONS.get(team.status, [])
    ctx = {
        "page_title": f"Team: {team.name}",
        "nav_section": "teams",
        "team": team,
        "players": team.players.all(),
        "matches": team_matches,
        "status_choices": TEAM_STATUS_CHOICES,
        "next_statuses": next_statuses,
    }
    return render(request, "panel/team_detail.html", ctx)


@staff_member_required(login_url="/panel/login/")
def team_create_view(request):
    if request.method == "POST":
        form = AdminTeamForm(request.POST)
        formset = PlayerInlineFormSet(request.POST, prefix="players")
        if form.is_valid() and formset.is_valid():
            team = form.save()
            formset.instance = team
            formset.save()
            messages.success(request, f'Team "{team.name}" created.')
            return redirect("panel:team_detail", pk=team.pk)
    else:
        form = AdminTeamForm()
        formset = PlayerInlineFormSet(prefix="players")

    ctx = {
        "page_title": "Create Team",
        "nav_section": "teams",
        "form": form,
        "formset": formset,
        "is_edit": False,
    }
    return render(request, "panel/team_form.html", ctx)


@staff_member_required(login_url="/panel/login/")
def team_edit_view(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        form = AdminTeamForm(request.POST, instance=team)
        formset = PlayerInlineFormSet(request.POST, instance=team, prefix="players")
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Team "{team.name}" updated.')
            return redirect("panel:team_detail", pk=team.pk)
    else:
        form = AdminTeamForm(instance=team)
        formset = PlayerInlineFormSet(instance=team, prefix="players")

    ctx = {
        "page_title": f"Edit: {team.name}",
        "nav_section": "teams",
        "form": form,
        "formset": formset,
        "team": team,
        "is_edit": True,
    }
    return render(request, "panel/team_form.html", ctx)


@staff_member_required(login_url="/panel/login/")
def team_delete_view(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        name = team.name
        team.delete()
        messages.success(request, f'Team "{name}" deleted.')
        return redirect("panel:teams")
    ctx = {"page_title": f"Delete: {team.name}", "nav_section": "teams", "team": team}
    return render(request, "panel/team_confirm_delete.html", ctx)


# ── Team Status Workflow ─────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def team_status_action(request, pk):
    """Change a single team's status (must be POST)."""
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("new_status", "")
        allowed = _STATUS_TRANSITIONS.get(team.status, [])
        if new_status in allowed:
            old_display = team.get_status_display()
            team.status = new_status
            team.save(update_fields=["status"])
            messages.success(
                request,
                f'"{team.name}" status changed: {old_display} → {team.get_status_display()}',
            )
        else:
            messages.error(request, f"Cannot change status to {new_status}.")
    return redirect("panel:team_detail", pk=pk)


@staff_member_required(login_url="/panel/login/")
@require_POST
def generate_roster_code(request, pk):
    """Generate a random 6-digit roster access code for a team."""
    import random

    from .constants import ROSTER_CODE_LENGTH

    team = get_object_or_404(Team, pk=pk)
    code = "".join(str(random.randint(0, 9)) for _ in range(ROSTER_CODE_LENGTH))
    team.roster_code = code
    team.save(update_fields=["roster_code"])
    messages.success(request, f'Roster code for "{team.name}": {code}')
    return redirect("panel:team_detail", pk=pk)


@staff_member_required(login_url="/panel/login/")
def team_batch_action(request):
    """Apply a status action to multiple selected teams."""
    if request.method != "POST":
        return redirect("panel:teams")

    action = request.POST.get("batch_action", "")
    team_ids = request.POST.getlist("team_ids")
    if not team_ids or not action:
        messages.error(request, "Select teams and an action.")
        return redirect("panel:teams")

    # Map batch action names to target status
    action_map = {
        "mark_awaiting": TEAM_STATUS_AWAITING_PAYMENT,
        "mark_paid": TEAM_STATUS_PAID,
        "approve": TEAM_STATUS_APPROVED,
        "reset": TEAM_STATUS_REGISTERED,
    }
    target = action_map.get(action)
    if not target:
        messages.error(request, "Unknown action.")
        return redirect("panel:teams")

    teams = Team.objects.filter(pk__in=team_ids)
    updated = 0
    skipped = 0
    for team in teams:
        allowed = _STATUS_TRANSITIONS.get(team.status, [])
        if target in allowed or action == "reset":
            team.status = target
            team.save(update_fields=["status"])
            updated += 1
        else:
            skipped += 1

    label = dict(TEAM_STATUS_CHOICES).get(target, target)
    msg = f"{updated} team(s) updated to {label}."
    if skipped:
        msg += f" {skipped} skipped (invalid transition)."
    messages.success(request, msg)
    return redirect("panel:teams")


# ── Check-in ─────────────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def checkin_view(request):
    """Game-day check-in page — lists all APPROVED teams."""
    teams = Team.objects.filter(status=TEAM_STATUS_APPROVED).order_by("group_name", "name")
    total = teams.count()
    checked = teams.filter(checked_in=True).count()
    ctx = {
        "page_title": "Check-in",
        "nav_section": "checkin",
        "teams": teams,
        "total": total,
        "checked": checked,
    }
    return render(request, "panel/checkin.html", ctx)


@staff_member_required(login_url="/panel/login/")
@require_POST
def checkin_toggle(request, pk):
    """AJAX endpoint — toggle checked_in for a team. Returns JSON."""
    team = get_object_or_404(Team, pk=pk, status=TEAM_STATUS_APPROVED)
    team.checked_in = not team.checked_in
    team.save(update_fields=["checked_in"])
    total = Team.objects.filter(status=TEAM_STATUS_APPROVED).count()
    checked = Team.objects.filter(status=TEAM_STATUS_APPROVED, checked_in=True).count()
    return JsonResponse({
        "ok": True,
        "checked_in": team.checked_in,
        "team_name": team.name,
        "checked": checked,
        "total": total,
    })


# ── Schedule ─────────────────────────────────────────────


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

    # Build grid data: rows=timeslots, cols=courts
    grid_data = []
    if view_mode == "grid":
        from collections import OrderedDict

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
        "stage_filter": stage,
        "status_filter": status,
        "court_filter": court,
        "group_filter": group,
        "view_mode": view_mode,
        "grid_data": grid_data,
        "courts": COURT_CHOICES,
        "stage_choices": STAGE_CHOICES,
        "match_status_choices": MATCH_STATUS_CHOICES,
        "groups": groups,
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
    from .services import import_schedule_csv, parse_schedule_csv

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


# ── Stats ────────────────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def stats_list_view(request):
    """List matches with stats-import status indicator."""
    matches = (
        Match.objects.select_related("team_a", "team_b")
        .order_by("-match_number")
    )
    stage_filter = request.GET.get("stage", "")
    imported_filter = request.GET.get("imported", "")

    if stage_filter:
        matches = matches.filter(stage=stage_filter)
    if imported_filter == "yes":
        matches = matches.filter(stats_imported=True)
    elif imported_filter == "no":
        matches = matches.filter(stats_imported=False)

    return render(request, "panel/stats_list.html", {
        "page_title": "Statistics",
        "nav_section": "stats",
        "matches": matches,
        "stage_filter": stage_filter,
        "imported_filter": imported_filter,
        "STAGE_CHOICES": STAGE_CHOICES,
    })


@staff_member_required(login_url="/panel/login/")
def stats_import_view(request, pk):
    """Two-step CSV stats import: upload → preview → confirm (per-team)."""
    import io

    from .services import confirm_csv_import, preview_csv_import

    match = get_object_or_404(
        Match.objects.select_related("team_a", "team_b"), pk=pk
    )

    preview_rows = None
    errors = []
    warnings = []
    imported_count = None
    selected_team = None

    # Per-team import status
    team_a_imported = (
        match.team_a
        and PlayerMatchStats.objects.filter(match=match, team=match.team_a).exists()
    )
    team_b_imported = (
        match.team_b
        and PlayerMatchStats.objects.filter(match=match, team=match.team_b).exists()
    )

    if request.method == "POST":
        if "confirm" in request.POST:
            # ── Step 2: Confirm import from cached CSV ──
            cached_csv = request.session.pop("_stats_csv_content", None)
            cached_match = request.session.pop("_stats_csv_match", None)
            cached_team = request.session.pop("_stats_csv_team", None)
            if not cached_csv or cached_match != pk:
                messages.error(
                    request, "Session expired. Please upload the file again."
                )
            else:
                try:
                    file_obj = io.StringIO(cached_csv)
                    result = confirm_csv_import(file_obj, pk, cached_team)
                    imported_count = result["imported"]
                    warnings = result.get("warnings", [])
                    if cached_team:
                        selected_team = Team.objects.filter(pk=cached_team).first()
                    # Refresh per-team status after import
                    team_a_imported = (
                        match.team_a
                        and PlayerMatchStats.objects.filter(
                            match=match, team=match.team_a
                        ).exists()
                    )
                    team_b_imported = (
                        match.team_b
                        and PlayerMatchStats.objects.filter(
                            match=match, team=match.team_b
                        ).exists()
                    )
                    team_label = selected_team.name if selected_team else "all"
                    messages.success(
                        request,
                        f"Imported {imported_count} player stats "
                        f"({team_label}) for M{match.match_number}.",
                    )
                except ValueError as exc:
                    errors = [str(exc)]
        else:
            # ── Step 1: Upload + preview ──
            csv_file = request.FILES.get("csv_file")
            team_id_str = request.POST.get("team_id", "")
            if not csv_file:
                messages.error(request, "Please select a CSV file.")
            elif not team_id_str:
                messages.error(request, "Please select a team.")
            else:
                try:
                    team_id = int(team_id_str)
                except (ValueError, TypeError):
                    team_id = None
                if team_id is None:
                    messages.error(request, "Invalid team selection.")
                else:
                    selected_team = Team.objects.filter(pk=team_id).first()
                    raw = csv_file.read()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8-sig")
                    csv_file.seek(0)

                    result = preview_csv_import(csv_file, pk, team_id)
                    errors = result["errors"]
                    warnings = result["warnings"]

                    if result["can_import"]:
                        preview_rows = result["preview"]
                        # Cache raw CSV text in session for confirm step
                        request.session["_stats_csv_content"] = raw
                        request.session["_stats_csv_match"] = pk
                        request.session["_stats_csv_team"] = team_id

    return render(request, "panel/stats_import.html", {
        "page_title": f"Import Stats — M{match.match_number}",
        "nav_section": "stats",
        "match": match,
        "preview_rows": preview_rows,
        "errors": errors,
        "warnings": warnings,
        "imported_count": imported_count,
        "selected_team": selected_team,
        "team_a_imported": team_a_imported,
        "team_b_imported": team_b_imported,
    })


@staff_member_required(login_url="/panel/login/")
def stats_detail_view(request, pk):
    """View imported stats for a match, grouped by team."""
    match = get_object_or_404(
        Match.objects.select_related("team_a", "team_b"), pk=pk
    )
    stats_a = (
        PlayerMatchStats.objects.filter(match=match, team=match.team_a)
        .select_related("player")
        .order_by("jersey_number")
        if match.team_a
        else []
    )
    stats_b = (
        PlayerMatchStats.objects.filter(match=match, team=match.team_b)
        .select_related("player")
        .order_by("jersey_number")
        if match.team_b
        else []
    )
    team_stats_a = (
        TeamMatchStats.objects.filter(match=match, team=match.team_a).first()
        if match.team_a
        else None
    )
    team_stats_b = (
        TeamMatchStats.objects.filter(match=match, team=match.team_b).first()
        if match.team_b
        else None
    )

    return render(request, "panel/stats_detail.html", {
        "page_title": f"Stats — M{match.match_number}",
        "nav_section": "stats",
        "match": match,
        "stats_a": stats_a,
        "stats_b": stats_b,
        "team_stats_a": team_stats_a,
        "team_stats_b": team_stats_b,
    })


# Editable stat fields in order
_STAT_FIELDS = [
    "serve_attempts", "aces", "serve_errors",
    "kills", "attack_errors",
    "pass_errors",
    "blocks", "assists", "setting_errors",
]


@staff_member_required(login_url="/panel/login/")
def stats_edit_view(request, pk):
    """Inline-edit player stats for a match, then recalculate aggregates."""
    from .services import (
        _aggregate_team_stats,
        recalculate_dream_team,
        recalculate_standings,
    )

    match = get_object_or_404(
        Match.objects.select_related("team_a", "team_b"), pk=pk
    )
    player_stats = (
        PlayerMatchStats.objects.filter(match=match)
        .select_related("player", "team")
        .order_by("team__name", "jersey_number")
    )

    if request.method == "POST":
        errors = []
        for ps in player_stats:
            for field in _STAT_FIELDS:
                key = f"stat_{ps.pk}_{field}"
                val = request.POST.get(key, "").strip()
                if val == "":
                    val = 0
                try:
                    int_val = int(val)
                    if int_val < 0:
                        raise ValueError
                except (ValueError, TypeError):
                    errors.append(
                        f"{ps.player} — {field}: invalid value '{request.POST.get(key, '')}'."
                    )
                    continue
                setattr(ps, field, int_val)

            # Position
            pos_key = f"stat_{ps.pk}_position"
            pos_val = request.POST.get(pos_key, ps.position).strip().upper()
            ps.position = pos_val

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            # Save all
            for ps in player_stats:
                ps.save()

            # Recalculate team aggregates
            TeamMatchStats.objects.filter(match=match).delete()
            _aggregate_team_stats(match)

            # Recalculate standings / dream team
            if match.stage == STAGE_GROUP:
                recalculate_standings()
            recalculate_dream_team()

            messages.success(
                request,
                f"Stats updated for M{match.match_number}. Aggregates recalculated.",
            )
            return redirect("panel:stats_detail", pk=pk)

    return render(request, "panel/stats_edit.html", {
        "page_title": f"Edit Stats — M{match.match_number}",
        "nav_section": "stats",
        "match": match,
        "player_stats": player_stats,
        "STAT_FIELDS": _STAT_FIELDS,
        "POSITION_CHOICES": POSITION_CHOICES,
    })


# ── Gallery ──────────────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def gallery_list_view(request):
    tab = request.GET.get("tab", "photos")
    photos = GalleryPhoto.objects.order_by("order", "-uploaded_at")
    videos = GalleryVideo.objects.order_by("order", "-uploaded_at")
    return render(request, "panel/gallery.html", {
        "page_title": "Gallery",
        "nav_section": "gallery",
        "photos": photos,
        "videos": videos,
        "tab": tab,
    })


@staff_member_required(login_url="/panel/login/")
def gallery_add_view(request):
    form = GalleryPhotoForm()
    if request.method == "POST":
        form = GalleryPhotoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Photo added.")
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Add Photo",
        "nav_section": "gallery",
        "form": form,
    })


@staff_member_required(login_url="/panel/login/")
def gallery_bulk_add_view(request):
    form = GalleryBulkForm()
    if request.method == "POST":
        form = GalleryBulkForm(request.POST)
        if form.is_valid():
            lines = form.cleaned_data["urls"].strip().splitlines()
            added = 0
            errors = []
            max_order = GalleryPhoto.objects.aggregate(m=Max("order"))["m"] or 0
            for line in lines:
                url = line.strip()
                if not url:
                    continue
                file_id = _parse_drive_file_id(url)
                if not file_id:
                    errors.append(f"Bad URL: {url[:60]}")
                    continue
                if GalleryPhoto.objects.filter(drive_file_id=file_id).exists():
                    errors.append(f"Duplicate: {file_id[:12]}…")
                    continue
                max_order += 1
                GalleryPhoto.objects.create(
                    drive_file_id=file_id,
                    drive_url=_drive_view_url(file_id),
                    thumbnail_url=_drive_thumbnail(file_id),
                    order=max_order,
                )
                added += 1
            if added:
                messages.success(request, f"{added} photo(s) added.")
            for err in errors:
                messages.warning(request, err)
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Bulk Add Photos",
        "nav_section": "gallery",
        "bulk_form": form,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def gallery_delete_view(request, pk):
    photo = get_object_or_404(GalleryPhoto, pk=pk)
    photo.delete()
    messages.success(request, "Photo deleted.")
    return redirect("panel:gallery")


@staff_member_required(login_url="/panel/login/")
@require_POST
def gallery_reorder_view(request):
    """AJAX endpoint — receives JSON array of photo IDs in new order."""
    try:
        order_ids = json.loads(request.body)
        if not isinstance(order_ids, list):
            return JsonResponse({"error": "Expected a list"}, status=400)
        for idx, photo_id in enumerate(order_ids):
            GalleryPhoto.objects.filter(pk=photo_id).update(order=idx)
        return JsonResponse({"ok": True})
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)


# ── Gallery Videos ───────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def video_add_view(request):
    form = GalleryVideoForm()
    if request.method == "POST":
        form = GalleryVideoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Video added.")
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Add Video",
        "nav_section": "gallery",
        "video_form": form,
    })


@staff_member_required(login_url="/panel/login/")
def video_edit_view(request, pk):
    video = get_object_or_404(GalleryVideo, pk=pk)
    form = GalleryVideoForm(instance=video)
    if request.method == "POST":
        form = GalleryVideoForm(request.POST, instance=video)
        if form.is_valid():
            form.save()
            messages.success(request, "Video updated.")
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Edit Video",
        "nav_section": "gallery",
        "video_form": form,
        "video": video,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def video_delete_view(request, pk):
    video = get_object_or_404(GalleryVideo, pk=pk)
    video.delete()
    messages.success(request, "Video deleted.")
    return redirect("panel:gallery")


@staff_member_required(login_url="/panel/login/")
@require_POST
def video_reorder_view(request):
    """AJAX endpoint — receives JSON array of video IDs in new order."""
    try:
        order_ids = json.loads(request.body)
        if not isinstance(order_ids, list):
            return JsonResponse({"error": "Expected a list"}, status=400)
        for idx, vid_id in enumerate(order_ids):
            GalleryVideo.objects.filter(pk=vid_id).update(order=idx)
        return JsonResponse({"ok": True})
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)


# ── Dream Team ───────────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def dreamteam_view(request):
    """Display / manually edit the Dream Team 7-slot court."""
    SLOTS = [
        ("front-left", "OH", "Outside Hitter"),
        ("front-center", "MB", "Middle Blocker"),
        ("front-right", "OPP", "Opposite"),
        ("back-left", "S", "Setter"),
        ("back-center", "MB", "Middle Blocker"),
        ("back-right", "OH", "Outside Hitter"),
        ("libero", "L", "Libero"),
    ]

    if request.method == "POST":
        DreamTeamEntry.objects.all().delete()
        entries = []
        for slot_id, default_pos, _label in SLOTS:
            player_id = request.POST.get(f"player_{slot_id}")
            if not player_id:
                continue
            player = Player.objects.filter(pk=player_id).select_related("team").first()
            if not player:
                continue
            metric_label = request.POST.get(f"metric_label_{slot_id}", "")
            metric_value = request.POST.get(f"metric_value_{slot_id}", "0")
            try:
                metric_value = float(metric_value)
            except (ValueError, TypeError):
                metric_value = 0
            entries.append(
                DreamTeamEntry(
                    position=default_pos,
                    slot=slot_id,
                    player=player,
                    team=player.team,
                    metric_label=metric_label,
                    metric_value=metric_value,
                    is_auto=False,
                )
            )
        DreamTeamEntry.objects.bulk_create(entries)
        messages.success(request, f"Dream Team saved ({len(entries)} slots).")
        return redirect("panel:dreamteam")

    # Build current entries keyed by slot
    current = {e.slot: e for e in DreamTeamEntry.objects.select_related("player", "team").all()}
    players = Player.objects.select_related("team").order_by("team__name", "last_name", "first_name")

    slots_data = []
    for slot_id, default_pos, label in SLOTS:
        entry = current.get(slot_id)
        slots_data.append({
            "slot_id": slot_id,
            "position": default_pos,
            "label": label,
            "entry": entry,
        })

    return render(request, "panel/dreamteam.html", {
        "page_title": "Dream Team",
        "nav_section": "dreamteam",
        "slots": slots_data,
        "players": players,
        "has_entries": bool(current),
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def dreamteam_autofill_view(request):
    """Recalculate dream team from stats (auto-fill)."""
    from .services import recalculate_dream_team

    recalculate_dream_team()
    messages.success(request, "Dream Team auto-filled from player stats.")
    return redirect("panel:dreamteam")


@staff_member_required(login_url="/panel/login/")
@require_POST
def dreamteam_reset_view(request):
    """Delete all Dream Team entries."""
    deleted, _ = DreamTeamEntry.objects.all().delete()
    messages.success(request, f"Dream Team cleared ({deleted} entries removed).")
    return redirect("panel:dreamteam")
