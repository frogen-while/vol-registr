"""Rankings — group standings tables + category leaders + recalculate."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..constants import (
    POSITION_L,
    POSITION_MB,
    POSITION_OH,
    POSITION_OPP,
    POSITION_S,
)
from ..models import GroupStanding, PlayerMatchStats


@staff_member_required(login_url="/panel/login/")
def rankings_view(request):
    """Standings tables per group + category leaders."""
    # ── Group Standings ──────────────────────────────────
    standings = (
        GroupStanding.objects
        .select_related("team")
        .order_by("group", "rank_in_group")
    )
    groups: dict[str, list] = {}
    for gs in standings:
        groups.setdefault(gs.group, []).append(gs)

    # ── Category Leaders (top-5 each) ────────────────────
    def _leaders(metric_field, label, positions=None):
        qs = PlayerMatchStats.objects.values(
            "player_id",
            "player__first_name",
            "player__last_name",
            "player__jersey_number",
            "team__name",
        )
        if positions:
            qs = qs.filter(position__in=positions)
        return list(
            qs.annotate(total=Sum(metric_field))
            .order_by("-total")
            .filter(total__gt=0)[:5]
        )

    leaders = [
        {
            "key": "scorers",
            "label": "Top Scorers",
            "icon": "fa-volleyball-ball",
            "metric": "kills",
            "rows": _leaders("kills", "kills"),
        },
        {
            "key": "servers",
            "label": "Best Servers",
            "icon": "fa-hand-point-up",
            "metric": "aces",
            "rows": _leaders("aces", "aces"),
        },
        {
            "key": "blockers",
            "label": "Top Blockers",
            "icon": "fa-shield-alt",
            "metric": "blocks",
            "rows": _leaders("blocks", "blocks", positions=[POSITION_MB]),
        },
        {
            "key": "passers",
            "label": "Best Passers",
            "icon": "fa-hands",
            "metric": "perfect_passes",
            "rows": _leaders("perfect_passes", "perfect_passes", positions=[POSITION_L, POSITION_OH]),
        },
        {
            "key": "setters",
            "label": "Top Setters",
            "icon": "fa-magic",
            "metric": "assists",
            "rows": _leaders("assists", "assists", positions=[POSITION_S]),
        },
    ]

    return render(request, "panel/rankings.html", {
        "page_title": "Rankings",
        "nav_section": "rankings",
        "groups": groups,
        "leaders": leaders,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def rankings_recalculate_view(request):
    """Recalculate all standings."""
    from ..services import recalculate_standings

    recalculate_standings()
    standings_count = GroupStanding.objects.count()
    messages.success(
        request,
        f"Recalculated standings for {standings_count} teams.",
    )
    return redirect("panel:rankings")
