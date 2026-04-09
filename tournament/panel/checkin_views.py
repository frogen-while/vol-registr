"""Check-in views — game-day attendance tracking with search and arrival cards."""

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from ..constants import TEAM_STATUS_APPROVED
from ..models import AUDIT_CATEGORY_CHECKIN, Team
from .audit import log_audit


@staff_member_required(login_url="/panel/login/")
def checkin_view(request):
    """Game-day check-in desk — lists APPROVED teams with search and arrival cards."""
    teams = (
        Team.objects.filter(status=TEAM_STATUS_APPROVED)
        .prefetch_related("players")
        .order_by("group_name", "name")
    )
    total = teams.count()
    checked = sum(1 for t in teams if t.checked_in)
    # Split into warning (incomplete readiness) and ready groups
    warning_teams = [t for t in teams if t.readiness_score < 5 and not t.checked_in]
    ctx = {
        "page_title": "Check-in Desk",
        "nav_section": "checkin",
        "teams": teams,
        "total": total,
        "checked": checked,
        "warning_teams": warning_teams,
    }
    return render(request, "panel/checkin.html", ctx)


@staff_member_required(login_url="/panel/login/")
def checkin_search(request):
    """AJAX — instant search by team name or captain name. Returns JSON list."""
    q = request.GET.get("q", "").strip()
    if len(q) < 1:
        return JsonResponse({"results": []})
    teams = (
        Team.objects.filter(status=TEAM_STATUS_APPROVED)
        .filter(
            Q(name__icontains=q)
            | Q(cap_name__icontains=q)
            | Q(cap_surname__icontains=q)
        )
        .prefetch_related("players")
        .order_by("name")[:20]
    )
    results = []
    for t in teams:
        player_count = t.players.count()
        results.append({
            "pk": t.pk,
            "name": t.name,
            "group": t.group_name or "—",
            "captain": f"{t.cap_name} {t.cap_surname}",
            "cap_phone": t.cap_phone or "",
            "player_count": player_count,
            "readiness_score": t.readiness_score,
            "is_payment_ok": t.is_payment_ok,
            "is_roster_complete": t.is_roster_complete,
            "is_contacts_complete": t.is_contacts_complete,
            "is_logo_uploaded": t.is_logo_uploaded,
            "has_duplicate_jerseys": t.has_duplicate_jerseys,
            "checked_in": t.checked_in,
            "toggle_url": f"/panel/checkin/{t.pk}/toggle/",
        })
    return JsonResponse({"results": results})


@staff_member_required(login_url="/panel/login/")
@require_POST
def checkin_toggle(request, pk):
    """AJAX endpoint — toggle checked_in for a team. Returns JSON."""
    team = get_object_or_404(Team, pk=pk, status=TEAM_STATUS_APPROVED)
    team.checked_in = not team.checked_in
    team.save(update_fields=["checked_in"])
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_CHECKIN,
        action="Checked in" if team.checked_in else "Check-in reverted",
        entity_type="Team", entity_id=team.pk, entity_label=team.name,
    )
    total = Team.objects.filter(status=TEAM_STATUS_APPROVED).count()
    checked = Team.objects.filter(status=TEAM_STATUS_APPROVED, checked_in=True).count()
    return JsonResponse({
        "ok": True,
        "checked_in": team.checked_in,
        "team_name": team.name,
        "checked": checked,
        "total": total,
    })
