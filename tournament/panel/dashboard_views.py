"""Control Room — operational dashboard replacing the old KPI page."""

import datetime as _dt

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from ..constants import (
    MATCH_FINISHED,
    MATCH_SCHEDULED,
    TEAM_STATUS_APPROVED,
    TEAM_STATUS_AWAITING_PAYMENT,
    TEAM_STATUS_PAID,
)
from ..models import GalleryPhoto, GalleryVideo, Match, Player, Team


@staff_member_required(login_url="/panel/login/")
def dashboard_view(request):
    now = timezone.now()
    two_hours = now + _dt.timedelta(hours=2)

    # ── KPI totals (kept for backward compat) ────────────
    teams_total = Team.objects.count()
    teams_by_status = dict(
        Team.objects.values_list("status")
        .annotate(c=Count("id"))
        .values_list("status", "c")
    )
    players_total = Player.objects.count()
    matches_total = Match.objects.count()
    matches_finished = Match.objects.filter(status=MATCH_FINISHED).count()
    matches_remaining = matches_total - matches_finished
    gallery_count = GalleryPhoto.objects.count() + GalleryVideo.objects.count()

    # ── Check-in numbers ─────────────────────────────────
    approved_teams = Team.objects.filter(status=TEAM_STATUS_APPROVED)
    checkin_of = approved_teams.count()
    checkin_count = approved_teams.filter(checked_in=True).count()

    # ── Alerts ───────────────────────────────────────────
    alerts = []

    # Approved but not checked-in
    not_checked_in = approved_teams.filter(checked_in=False).count()
    if not_checked_in:
        alerts.append({
            "level": "warning",
            "icon": "fas fa-user-clock",
            "text": f"{not_checked_in} approved team(s) not checked in",
            "url": "/panel/checkin/",
        })

    # Finished matches without stats
    no_stats = Match.objects.filter(
        status=MATCH_FINISHED, stats_imported=False
    ).count()
    if no_stats:
        alerts.append({
            "level": "critical",
            "icon": "fas fa-exclamation-triangle",
            "text": f"{no_stats} finished match(es) missing stats",
            "url": "/panel/stats/",
        })

    # Matches starting within 2 hours
    starting_soon = Match.objects.filter(
        status=MATCH_SCHEDULED,
        start_time__gte=now,
        start_time__lte=two_hours,
    ).count()
    if starting_soon:
        alerts.append({
            "level": "info",
            "icon": "fas fa-clock",
            "text": f"{starting_soon} match(es) starting within 2 hours",
            "url": "/panel/schedule/",
        })

    # Teams awaiting payment
    awaiting_payment = Team.objects.filter(
        status=TEAM_STATUS_AWAITING_PAYMENT
    ).count()
    if awaiting_payment:
        alerts.append({
            "level": "warning",
            "icon": "fas fa-credit-card",
            "text": f"{awaiting_payment} team(s) awaiting payment",
            "url": "/panel/teams/?status=AWAITING_PAYMENT",
        })

    # Paid but not yet approved
    paid_not_approved = Team.objects.filter(status=TEAM_STATUS_PAID).count()
    if paid_not_approved:
        alerts.append({
            "level": "info",
            "icon": "fas fa-check-circle",
            "text": f"{paid_not_approved} paid team(s) pending approval",
            "url": "/panel/teams/?status=PAID",
        })

    # ── Queue cards ──────────────────────────────────────
    queues = []

    if no_stats:
        queue_matches = (
            Match.objects.filter(status=MATCH_FINISHED, stats_imported=False)
            .select_related("team_a", "team_b")
            .order_by("match_number")[:5]
        )
        for m in queue_matches:
            queues.append({
                "urgency": "critical",
                "icon": "fas fa-file-import",
                "title": f"Import stats — M{m.match_number}",
                "detail": f"{m.team_a or 'TBD'} vs {m.team_b or 'TBD'}",
                "url": f"/panel/stats/{m.pk}/import/",
            })

    if not_checked_in:
        queues.append({
            "urgency": "warning",
            "icon": "fas fa-clipboard-check",
            "title": f"Check in {not_checked_in} team(s)",
            "detail": "Approved teams awaiting check-in",
            "url": "/panel/checkin/",
        })

    if awaiting_payment:
        queues.append({
            "urgency": "info",
            "icon": "fas fa-credit-card",
            "title": f"Review {awaiting_payment} payment(s)",
            "detail": "Teams awaiting payment confirmation",
            "url": "/panel/teams/?status=AWAITING_PAYMENT",
        })

    # ── Timeline — next 2 hours ──────────────────────────
    timeline_matches = (
        Match.objects.filter(
            start_time__gte=now,
            start_time__lte=two_hours,
        )
        .select_related("team_a", "team_b")
        .order_by("start_time", "court")
    )

    # ── Intelligence column ──────────────────────────────
    checkin_pct = (
        round(checkin_count / checkin_of * 100) if checkin_of > 0 else 0
    )
    stats_total = Match.objects.filter(status=MATCH_FINISHED).count()
    stats_done = Match.objects.filter(
        status=MATCH_FINISHED, stats_imported=True
    ).count()
    stats_pct = round(stats_done / stats_total * 100) if stats_total > 0 else 0

    # ── Live widgets: matches today, LIVE now, next match ─
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + _dt.timedelta(days=1)
    matches_today = Match.objects.filter(
        start_time__gte=today_start, start_time__lt=today_end,
    ).count()
    matches_live = Match.objects.filter(status="LIVE").count()
    next_match = (
        Match.objects.filter(status=MATCH_SCHEDULED, start_time__gte=now)
        .select_related("team_a", "team_b")
        .order_by("start_time")
        .first()
    )

    recent_teams = Team.objects.order_by("-created_at")[:5]

    ctx = {
        "page_title": "Control Room",
        "nav_section": "dashboard",
        # KPIs
        "teams_total": teams_total,
        "teams_by_status": teams_by_status,
        "players_total": players_total,
        "checkin_count": checkin_count,
        "checkin_of": checkin_of,
        "matches_total": matches_total,
        "matches_finished": matches_finished,
        "matches_remaining": matches_remaining,
        "gallery_count": gallery_count,
        # Alerts
        "alerts": alerts,
        # Queues
        "queues": queues,
        # Timeline
        "timeline_matches": timeline_matches,
        "now": now,
        # Intelligence
        "checkin_pct": checkin_pct,
        "stats_pct": stats_pct,
        "stats_done": stats_done,
        "stats_total": stats_total,
        # Recent
        "recent_teams": recent_teams,
        # Live widgets
        "matches_today": matches_today,
        "matches_live": matches_live,
        "next_match": next_match,
    }
    return render(request, "panel/control_room.html", ctx)
