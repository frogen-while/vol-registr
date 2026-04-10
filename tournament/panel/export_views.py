"""CSV export views — standings, player stats, match results."""

import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from ..models import GroupStanding, Match, PlayerMatchStats


@staff_member_required(login_url="/panel/login/")
def export_standings_csv(request):
    """Export group standings as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="standings.csv"'
    writer = csv.writer(response)
    writer.writerow(["Group", "Rank", "Team", "Played", "Wins", "Losses", "Sets Won", "Sets Lost", "Points"])
    for s in GroupStanding.objects.select_related("team").order_by("group", "rank_in_group"):
        writer.writerow([
            s.group, s.rank_in_group, s.team.name,
            s.played, s.wins, s.losses, s.sets_won, s.sets_lost, s.points,
        ])
    return response


@staff_member_required(login_url="/panel/login/")
def export_player_stats_csv(request):
    """Export aggregated player stats as CSV."""
    from django.db.models import Sum

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="player_stats.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Player", "Team", "Position", "Jersey", "Matches",
        "Points", "Kills", "Aces", "Blocks", "Assists",
        "Serve Errors", "Attack Errors",
    ])
    qs = (
        PlayerMatchStats.objects
        .values(
            "player__first_name", "player__last_name",
            "team__name", "position", "jersey_number",
        )
        .annotate(
            matches=Sum("sets_played"),  # rough proxy
            total_kills=Sum("kills"),
            total_aces=Sum("aces"),
            total_blocks=Sum("blocks"),
            total_assists=Sum("assists"),
            total_serve_errors=Sum("serve_errors"),
            total_attack_errors=Sum("attack_errors"),
        )
        .order_by("team__name", "player__last_name")
    )
    for r in qs:
        pts = (r["total_kills"] or 0) + (r["total_aces"] or 0) + (r["total_blocks"] or 0)
        writer.writerow([
            f"{r['player__first_name']} {r['player__last_name']}",
            r["team__name"],
            r["position"],
            r["jersey_number"],
            r["matches"] or 0,
            pts,
            r["total_kills"] or 0,
            r["total_aces"] or 0,
            r["total_blocks"] or 0,
            r["total_assists"] or 0,
            r["total_serve_errors"] or 0,
            r["total_attack_errors"] or 0,
        ])
    return response


@staff_member_required(login_url="/panel/login/")
def export_results_csv(request):
    """Export match results as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="match_results.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Match #", "Stage", "Group", "Court", "Start Time",
        "Team A", "Team B", "Score A", "Score B", "Status",
    ])
    for m in Match.objects.select_related("team_a", "team_b").order_by("match_number"):
        writer.writerow([
            m.match_number,
            m.get_stage_display(),
            m.group or "",
            m.get_court_display(),
            m.start_time.strftime("%Y-%m-%d %H:%M") if m.start_time else "",
            m.display_name_a,
            m.display_name_b,
            m.score_a,
            m.score_b,
            m.get_status_display(),
        ])
    return response
