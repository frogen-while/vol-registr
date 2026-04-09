"""Team CRUD, status workflow, batch actions, roster codes, drawer, pipeline."""

import random

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from ..admin_forms import AdminTeamForm, PlayerInlineFormSet
from ..constants import (
    PAYMENT_STATUS_CHOICES,
    ROSTER_CODE_LENGTH,
    TEAM_STATUS_APPROVED,
    TEAM_STATUS_AWAITING_PAYMENT,
    TEAM_STATUS_CHOICES,
    TEAM_STATUS_PAID,
    TEAM_STATUS_REGISTERED,
)
from ..models import AUDIT_CATEGORY_TEAM, AuditEntry, Match, Team
from .audit import log_audit

# Allowed status transitions: current → list of valid next statuses
_STATUS_TRANSITIONS = {
    TEAM_STATUS_REGISTERED: [TEAM_STATUS_AWAITING_PAYMENT],
    TEAM_STATUS_AWAITING_PAYMENT: [TEAM_STATUS_PAID, TEAM_STATUS_REGISTERED],
    TEAM_STATUS_PAID: [TEAM_STATUS_APPROVED, TEAM_STATUS_AWAITING_PAYMENT],
    TEAM_STATUS_APPROVED: [TEAM_STATUS_PAID],
}


@staff_member_required(login_url="/panel/login/")
def teams_list_view(request):
    qs = Team.objects.annotate(player_count=Count("players")).prefetch_related("players")

    # ── Filters ──
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    payment = request.GET.get("payment", "")
    group = request.GET.get("group", "")
    checkin = request.GET.get("checkin", "")
    readiness = request.GET.get("readiness", "")

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

    # ── Post-query readiness filter (property-based) ──
    teams = list(qs)
    if readiness == "incomplete":
        teams = [t for t in teams if t.readiness_score < 5]

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
        "teams": teams,
        "q": q,
        "status": status,
        "payment": payment,
        "group": group,
        "checkin": checkin,
        "readiness": readiness,
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
    audit_log = AuditEntry.objects.filter(
        entity_type="Team", entity_id=team.pk,
    ).select_related("user")[:15]
    ctx = {
        "page_title": f"Team: {team.name}",
        "nav_section": "teams",
        "team": team,
        "players": team.players.all(),
        "matches": team_matches,
        "status_choices": TEAM_STATUS_CHOICES,
        "next_statuses": next_statuses,
        "audit_log": audit_log,
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
            log_audit(
                user=request.user, category=AUDIT_CATEGORY_TEAM,
                action=f"Status changed: {old_display} → {team.get_status_display()}",
                entity_type="Team", entity_id=team.pk, entity_label=team.name,
            )
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
    team = get_object_or_404(Team, pk=pk)
    code = "".join(str(random.randint(0, 9)) for _ in range(ROSTER_CODE_LENGTH))
    team.roster_code = code
    team.save(update_fields=["roster_code"])
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_TEAM,
        action="Roster code generated",
        entity_type="Team", entity_id=team.pk, entity_label=team.name,
    )
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
        if team.status == target:
            skipped += 1
            continue
        team.status = target
        team.save(update_fields=["status"])
        updated += 1

    label = dict(TEAM_STATUS_CHOICES).get(target, target)
    msg = f"{updated} team(s) updated to {label}."
    if skipped:
        msg += f" {skipped} skipped (invalid transition)."
    messages.success(request, msg)
    return redirect("panel:teams")


# ── Team Drawer (AJAX partial) ───────────────────────────


@staff_member_required(login_url="/panel/login/")
def team_drawer_view(request, pk):
    """Return drawer HTML partial for a specific team."""
    team = get_object_or_404(Team.objects.prefetch_related("players"), pk=pk)
    recent_matches = (
        Match.objects.filter(Q(team_a=team) | Q(team_b=team))
        .select_related("team_a", "team_b")
        .order_by("-start_time")[:3]
    )
    next_statuses = _STATUS_TRANSITIONS.get(team.status, [])
    ctx = {
        "team": team,
        "players": team.players.all(),
        "recent_matches": recent_matches,
        "next_statuses": next_statuses,
        "status_choices": TEAM_STATUS_CHOICES,
    }
    html = render_to_string("panel/partials/team_drawer.html", ctx, request=request)
    return JsonResponse({"html": html})


# ── Pipeline Board ───────────────────────────────────────

_PIPELINE_COLUMNS = [
    (TEAM_STATUS_REGISTERED, "Registered", "gray"),
    (TEAM_STATUS_AWAITING_PAYMENT, "Awaiting Payment", "yellow"),
    (TEAM_STATUS_PAID, "Paid", "blue"),
    (TEAM_STATUS_APPROVED, "Approved", "green"),
]


@staff_member_required(login_url="/panel/login/")
def teams_pipeline_view(request):
    """Kanban-like pipeline board for team registration flow."""
    teams = Team.objects.annotate(player_count=Count("players")).prefetch_related(
        "players"
    )
    columns = []
    for status_val, label, color in _PIPELINE_COLUMNS:
        col_teams = list(teams.filter(status=status_val).order_by("name"))
        columns.append({
            "status": status_val,
            "label": label,
            "color": color,
            "teams": col_teams,
            "count": len(col_teams),
        })

    # Checked-in column (subset of APPROVED)
    checked = list(
        teams.filter(status=TEAM_STATUS_APPROVED, checked_in=True).order_by("name")
    )
    columns.append({
        "status": "CHECKED_IN",
        "label": "Checked In",
        "color": "cyan",
        "teams": checked,
        "count": len(checked),
    })

    ctx = {
        "page_title": "Teams Pipeline",
        "nav_section": "teams",
        "columns": columns,
        "status_transitions": {k: v for k, v in _STATUS_TRANSITIONS.items()},
    }
    return render(request, "panel/teams_pipeline.html", ctx)


@staff_member_required(login_url="/panel/login/")
@require_POST
def team_pipeline_move(request, pk):
    """Move a team to a new status from pipeline board (AJAX)."""
    team = get_object_or_404(Team, pk=pk)
    new_status = request.POST.get("new_status", "")
    allowed = _STATUS_TRANSITIONS.get(team.status, [])
    if new_status not in allowed:
        return JsonResponse({"ok": False, "error": "Invalid transition"}, status=400)
    team.status = new_status
    team.save(update_fields=["status"])
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_TEAM,
        action=f"Pipeline move → {dict(TEAM_STATUS_CHOICES).get(new_status, new_status)}",
        entity_type="Team", entity_id=team.pk, entity_label=team.name,
    )
    return JsonResponse({
        "ok": True,
        "new_status": new_status,
        "new_label": dict(TEAM_STATUS_CHOICES).get(new_status, new_status),
    })
