"""
Read-only service layer that converts DB models into template-ready dicts.

Every public function returns plain Python structures whose shape matches
the context variables the existing Jinja/Django templates already consume.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from django.db.models import Sum, F, Value, FloatField, IntegerField, Case, When
from django.db.models.functions import Cast

from .constants import (
    EVENT_TYPE_CHOICES,
    MATCH_FINISHED,
    MVP_MATCH,
    MVP_TOURNAMENT,
    STAGE_CHOICES,
    STAGE_GROUP,
)
from .models import (
    DreamTeamEntry,
    GameSet,
    GroupStanding,
    Match,
    MatchHighlight,
    MVPSelection,
    Player,
    PlayerMatchStats,
    ScheduleEvent,
    Team,
    TeamMatchStats,
)

# ── Helpers ──────────────────────────────────────────────

_STAGE_DISPLAY = dict(STAGE_CHOICES)


def _stage_label(stage: str, group: str = "") -> str:
    """Human-friendly stage name, e.g. 'Group A' or 'Quarter-Final'."""
    if stage == STAGE_GROUP and group:
        return f"Group {group}"
    return _STAGE_DISPLAY.get(stage, stage)


def _match_status_label(m: Match) -> str:
    if m.status == MATCH_FINISHED:
        return "FT"
    return m.get_status_display()


def _sets_label(won: int, lost: int) -> str:
    return f"{won}:{lost}"


def _safe_pct(num: int, den: int):
    if not den:
        return None
    return (num / den) * 100


def _pct_label(value) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}%"


def _points_won(kills: int, aces: int, blocks: int) -> int:
    return kills + aces + blocks


def _player_stat_dict(ps: PlayerMatchStats, *, image: str = "assets/team/vol/team.png") -> dict:
    """Convert a PlayerMatchStats row into a template-ready dict."""
    pw = _points_won(ps.kills, ps.aces, ps.blocks)

    return {
        "number": ps.jersey_number,
        "name": f"{ps.player.first_name} {ps.player.last_name}",
        "player_id": ps.player_id,
        "position": ps.position,
        "sets_played": ps.sets_played,
        "points_won": pw,
        "aces": ps.aces,
        "blocks": ps.blocks,
        "kills": ps.kills,
        "attack_errors": ps.attack_errors,
        "serve_attempts": ps.serve_attempts,
        "serve_errors": ps.serve_errors,
        "pass_errors": ps.pass_errors,
        "assists": ps.assists,
        "setting_errors": ps.setting_errors,
        "serve_impact": ps.aces - ps.serve_errors,
        "image": image,
    }


def _aggregate_players(player_dicts: list[dict]) -> dict:
    """Sum raw fields and compute derived metrics for a list of player dicts."""
    keys = (
        "serve_attempts", "aces", "serve_errors",
        "attack_errors", "kills",
        "pass_errors",
        "blocks", "assists", "setting_errors",
    )
    totals = {k: sum(p.get(k, 0) for p in player_dicts) for k in keys}
    totals["points_won"] = sum(p.get("points_won", 0) for p in player_dicts)
    return totals


def _comparison_row(label_key, label, home_val, away_val, home_disp, away_disp):
    mx = max(home_val, away_val, 1)
    return {
        "label_key": label_key,
        "label": label,
        "home": home_disp,
        "away": away_disp,
        "home_width": f"{(home_val / mx) * 100:.0f}%",
        "away_width": f"{(away_val / mx) * 100:.0f}%",
    }


# ── Player image helpers ─────────────────────────────────

_DEFAULT_PLAYER_IMAGE = "assets/team/vol/team.png"
_DEFAULT_TEAM_IMAGE = "assets/team/vol/team.png"


def _resolve_photo(photo_path: str) -> str:
    """Return photo_path if set, otherwise the default placeholder."""
    return photo_path if photo_path else _DEFAULT_PLAYER_IMAGE


# ── Public API ───────────────────────────────────────────


def get_tournament_summary() -> dict:
    """Quick aggregate stats for the tournament hub hero."""
    total_matches = Match.objects.count()
    finished = Match.objects.filter(status=MATCH_FINISHED).count()
    total_sets = GameSet.objects.count()
    total_teams = Team.objects.count()
    return {
        "total_matches": total_matches,
        "matches_played": finished,
        "total_sets": total_sets,
        "total_teams": total_teams,
    }


_EVENT_TYPE_DISPLAY = dict(EVENT_TYPE_CHOICES)


def get_schedule_slots() -> list[dict]:
    """
    Build time-grouped schedule for the tournament preview page.

    Merges matches and schedule events (opening, breaks, ceremony)
    into a single timeline sorted by start_time.

    Returns list of ``{time, games: [...], events: [...]}``.
    """
    matches = list(
        Match.objects
        .select_related("team_a", "team_b")
        .order_by("start_time", "court")
    )
    events = list(
        ScheduleEvent.objects.order_by("start_time")
    )

    if not matches and not events:
        return []

    # Build unified items list: (start_time, type, object)
    items = []
    for m in matches:
        items.append((m.start_time, "match", m))
    for e in events:
        items.append((e.start_time, "event", e))
    items.sort(key=lambda x: x[0])

    slots: list[dict] = []
    for start_time, group in groupby(items, key=lambda x: x[0]):
        time_label = start_time.strftime("%H:%M")
        games = []
        slot_events = []
        for _st, item_type, obj in group:
            if item_type == "match":
                m = obj
                score = f"{m.score_a}:{m.score_b}" if m.is_finished else "NEXT"
                games.append({
                    "court": f"Court {m.court}",
                    "stage": _stage_label(m.stage, m.group),
                    "stage_raw": m.stage,
                    "status_raw": m.status,
                    "home": m.display_name_a,
                    "home_logo": m.team_a.logo_path if m.team_a and m.team_a.logo_path else "",
                    "home_short": (m.display_name_a[:2]).upper(),
                    "home_id": m.team_a_id,
                    "away": m.display_name_b,
                    "away_logo": m.team_b.logo_path if m.team_b and m.team_b.logo_path else "",
                    "away_short": (m.display_name_b[:2]).upper(),
                    "away_id": m.team_b_id,
                    "score_home": str(m.score_a) if m.is_finished else "",
                    "score_away": str(m.score_b) if m.is_finished else "",
                    "score": score,
                    "status": _match_status_label(m),
                    "match_id": m.pk,
                })
            else:
                e = obj
                end_label = e.end_time.strftime("%H:%M") if e.end_time else ""
                slot_events.append({
                    "title": e.title,
                    "type": e.event_type,
                    "type_label": _EVENT_TYPE_DISPLAY.get(e.event_type, e.event_type),
                    "description": e.description or "",
                    "end_time": end_label,
                })
        slots.append({"time": time_label, "games": games, "events": slot_events})

    return slots


def get_standings(view: str = "groups") -> list[dict]:
    """
    Group-stage standings for the tournament hub.

    ``view='groups'``: list of ``{group: "Group A", rows: [...]}``.
    ``view='overall'``: flat ranked list.
    """
    qs = GroupStanding.objects.select_related("team").order_by("group", "rank_in_group")

    # Fallback: if no GroupStanding rows exist, build from Team model
    if not qs.exists():
        teams_with_group = Team.objects.filter(group_name__isnull=False).exclude(group_name="").order_by("group_name", "pk")
        all_teams = Team.objects.order_by("pk")

        if not all_teams.exists():
            return []

        def _team_row(t, rank=None):
            row = {
                "team_id": t.pk,
                "name": t.name,
                "short": (t.name[:2]).upper(),
                "logo": t.logo_path or "",
                "played": 0,
                "wins": 0,
                "losses": 0,
                "sets": "0:0",
                "points": 0,
            }
            if rank is not None:
                row["rank"] = rank
                row["group"] = t.group_name or "—"
            return row

        if view == "groups":
            if teams_with_group.exists():
                result = []
                for grp, grp_teams in groupby(teams_with_group, key=attrgetter("group_name")):
                    result.append({"group": f"Group {grp}", "rows": [_team_row(t) for t in grp_teams]})
                return result
            # No groups assigned — show all teams in one table
            return [{"group": "All Teams", "rows": [_team_row(t) for t in all_teams]}]

        # overall fallback
        if teams_with_group.exists():
            return [_team_row(t, i) for i, t in enumerate(teams_with_group, start=1)]
        return [_team_row(t, i) for i, t in enumerate(all_teams, start=1)]

    if view == "groups":
        result = []
        for grp, entries in groupby(qs, key=attrgetter("group")):
            rows = []
            for gs in entries:
                rows.append({
                    "team_id": gs.team_id,
                    "name": gs.team.name,
                    "short": (gs.team.name[:2]).upper(),
                    "logo": gs.team.logo_path or "",
                    "played": gs.played,
                    "wins": gs.wins,
                    "losses": gs.losses,
                    "sets": _sets_label(gs.sets_won, gs.sets_lost),
                    "points": gs.points,
                })
            result.append({"group": f"Group {grp}", "rows": rows})
        return result

    # overall
    all_gs = list(qs)
    ranked = sorted(
        all_gs,
        key=lambda gs: (
            gs.points,
            gs.wins,
            (gs.sets_won / gs.sets_lost) if gs.sets_lost else float("inf"),
        ),
        reverse=True,
    )
    return [
        {
            "rank": i,
            "team_id": gs.team_id,
            "name": gs.team.name,
            "logo": gs.team.logo_path or "",
            "group": gs.group,
            "played": gs.played,
            "wins": gs.wins,
            "losses": gs.losses,
            "sets": _sets_label(gs.sets_won, gs.sets_lost),
            "points": gs.points,
        }
        for i, gs in enumerate(ranked, start=1)
    ]


def get_match_detail(match_id: int) -> dict | None:
    """
    Full context dict for the match detail page.

    Returns ``None`` if match not found.
    """
    try:
        m = Match.objects.select_related("team_a", "team_b").get(pk=match_id)
    except Match.DoesNotExist:
        return None

    # Sets
    sets = GameSet.objects.filter(match=m).order_by("set_number")
    set_scores = [
        {
            "label": f"Set {s.set_number}",
            "home": s.score_a,
            "away": s.score_b,
            "winner": "home" if s.score_a > s.score_b else "away",
        }
        for s in sets
    ]

    # Player stats
    all_ps = (
        PlayerMatchStats.objects
        .filter(match=m)
        .select_related("player", "team")
        .order_by("-kills")
    )
    home_players = [
        _player_stat_dict(ps, image=_resolve_photo(ps.player.photo_path))
        for ps in all_ps if m.team_a and ps.team_id == m.team_a_id
    ]
    away_players = [
        _player_stat_dict(ps, image=_resolve_photo(ps.player.photo_path))
        for ps in all_ps if m.team_b and ps.team_id == m.team_b_id
    ]

    home_totals = _aggregate_players(home_players) if home_players else {}
    away_totals = _aggregate_players(away_players) if away_players else {}

    # Team comparison bars
    team_stats = []
    if home_totals and away_totals:
        team_stats = [
            _comparison_row(
                "match_page.stat_kills", "Kills",
                home_totals.get("kills", 0), away_totals.get("kills", 0),
                str(home_totals.get("kills", 0)), str(away_totals.get("kills", 0)),
            ),
            _comparison_row(
                "match_page.stat_aces", "Aces",
                home_totals.get("aces", 0), away_totals.get("aces", 0),
                str(home_totals.get("aces", 0)), str(away_totals.get("aces", 0)),
            ),
            _comparison_row(
                "match_page.stat_blocks", "Blocks",
                home_totals.get("blocks", 0), away_totals.get("blocks", 0),
                str(home_totals.get("blocks", 0)), str(away_totals.get("blocks", 0)),
            ),
        ]

    home_name = m.team_a.name if m.team_a else "TBD"
    away_name = m.team_b.name if m.team_b else "TBD"
    home_short = (m.team_a.name[:2]).upper() if m.team_a else "?"
    away_short = (m.team_b.name[:2]).upper() if m.team_b else "?"
    home_logo = (m.team_a.logo_path or "") if m.team_a else ""
    away_logo = (m.team_b.logo_path or "") if m.team_b else ""

    match_dict = {
        "competition": "Pocket Aces Spring Tournament",
        "stage": _stage_label(m.stage, m.group),
        "status": "Final" if m.is_finished else m.get_status_display(),
        "status_raw": m.status,
        "date": m.start_time.strftime("%d %b %Y"),
        "time": m.start_time.strftime("%H:%M"),
        "venue": "Rzgow, Szkolna 5",
        "court": f"Court {m.court}",
        "scoring": "2:0 = 3 · 2:1 = 2 · 1:2 = 1",
        "home": {"name": home_name, "short": home_short, "logo": home_logo, "sets": m.score_a, "team_id": m.team_a_id},
        "away": {"name": away_name, "short": away_short, "logo": away_logo, "sets": m.score_b, "team_id": m.team_b_id},
    }

    match_meta = [
        {"label_key": "match_page.meta_competition", "label": "Competition", "value": match_dict["competition"]},
        {"label_key": "match_page.meta_stage", "label": "Stage", "value": match_dict["stage"]},
        {"label_key": "match_page.meta_court", "label": "Court", "value": match_dict["court"]},
        {"label_key": "match_page.meta_scoring", "label": "Scoring", "value": match_dict["scoring"]},
    ]

    # Prev / next match navigation
    prev_match = (
        Match.objects.filter(match_number__lt=m.match_number)
        .order_by("-match_number")
        .values("pk", "match_number")
        .first()
    )
    next_match = (
        Match.objects.filter(match_number__gt=m.match_number)
        .order_by("match_number")
        .values("pk", "match_number")
        .first()
    )

    # Match MVP
    mvp_sel = (
        MVPSelection.objects
        .filter(mvp_type=MVP_MATCH, match=m)
        .select_related("player", "team")
        .first()
    )
    match_mvp = None
    if mvp_sel:
        match_mvp = {
            "name": f"{mvp_sel.player.first_name} {mvp_sel.player.last_name}",
            "player_id": mvp_sel.player.pk,
            "team": mvp_sel.team.name,
            "team_logo": mvp_sel.team.logo_path or "",
            "image": _resolve_photo(mvp_sel.player.photo_path),
            "reason": mvp_sel.reason,
        }

    # Match highlights
    hl_qs = MatchHighlight.objects.filter(match=m).order_by("order")
    match_highlights = [
        {"title": h.title, "copy": h.description, "match": match_dict["stage"]}
        for h in hl_qs
    ]

    # ── Stage Rail: surrounding matches in the same stage ──
    stage_matches_qs = (
        Match.objects
        .filter(stage=m.stage)
        .select_related("team_a", "team_b")
        .order_by("match_number")
    )
    stage_rail = []
    for sm in stage_matches_qs:
        sh = sm.team_a.name if sm.team_a else "TBD"
        sa = sm.team_b.name if sm.team_b else "TBD"
        sh_short = (sm.team_a.name[:2]).upper() if sm.team_a else "?"
        sa_short = (sm.team_b.name[:2]).upper() if sm.team_b else "?"
        score_txt = f"{sm.score_a}:{sm.score_b}" if sm.is_finished else "—"
        stage_rail.append({
            "match_id": sm.pk,
            "court": f"Court {sm.court}",
            "home": sh_short,
            "away": sa_short,
            "teams": f"{sh_short} vs {sa_short}",
            "score": score_txt,
            "is_current": sm.pk == m.pk,
            "is_finished": sm.is_finished,
        })

    # ── Storyline — editorial tag for the match ──
    storyline = None
    if m.is_finished and set_scores:
        total_sets = len(set_scores)
        winner_sets = m.score_a if m.score_a > m.score_b else m.score_b
        loser_sets = m.score_b if m.score_a > m.score_b else m.score_a
        if total_sets == 2 and loser_sets == 0:
            storyline = "Straight sets"
        elif total_sets == 3 and loser_sets == 0:
            storyline = "Straight sets"
        elif loser_sets > 0 and winner_sets == total_sets - loser_sets:
            last_set = set_scores[-1]
            margin = abs(last_set["home"] - last_set["away"])
            if margin <= 2:
                storyline = "Tiebreak finish"
            else:
                storyline = "Comeback"

    # ── Player leaders ──
    all_player_dicts = home_players + away_players

    def _pick_match_leader(players, key, label):
        if not players:
            return None
        best = max(players, key=lambda p: p.get(key, 0))
        if best.get(key, 0) == 0:
            return None
        return {
            "category": label,
            "name": best["name"],
            "value": best[key],
            "player_id": best["player_id"],
            "image": best["image"],
        }

    match_leaders = [
        ldr for ldr in [
            _pick_match_leader(all_player_dicts, "points_won", "Top Scorer"),
            _pick_match_leader(all_player_dicts, "aces", "Best Server"),
            _pick_match_leader(all_player_dicts, "blocks", "Top Blocker"),
            _pick_match_leader(all_player_dicts, "assists", "Best Setter"),
        ] if ldr is not None
    ]

    return {
        "match": match_dict,
        "match_meta": match_meta,
        "set_scores": set_scores,
        "team_stats": team_stats,
        "home_players": home_players,
        "away_players": away_players,
        "match_mvp": match_mvp,
        "match_highlights": match_highlights,
        "stage_rail": stage_rail,
        "storyline": storyline,
        "match_leaders": match_leaders,
        "prev_match_id": prev_match["pk"] if prev_match else None,
        "prev_match_number": prev_match["match_number"] if prev_match else None,
        "next_match_id": next_match["pk"] if next_match else None,
        "next_match_number": next_match["match_number"] if next_match else None,
    }


def get_team_detail(team_id: int) -> dict | None:
    """Full context dict for the team detail/stats page."""
    try:
        team = Team.objects.get(pk=team_id)
    except Team.DoesNotExist:
        return None

    # Roster: aggregate across all matches
    roster_stats = (
        PlayerMatchStats.objects
        .filter(team=team)
        .values("player_id", "player__first_name", "player__last_name", "player__photo_path", "position", "jersey_number")
        .annotate(
            total_kills=Sum("kills"),
            total_aces=Sum("aces"),
            total_blocks=Sum("blocks"),
            total_attack_errors=Sum("attack_errors"),
            total_serve_attempts=Sum("serve_attempts"),
            total_serve_errors=Sum("serve_errors"),
            total_pass_errors=Sum("pass_errors"),
            total_assists=Sum("assists"),
            total_setting_errors=Sum("setting_errors"),
        )
        .order_by("-total_kills")
    )

    matches_played_count = (
        Match.objects
        .filter(status=MATCH_FINISHED)
        .filter(team_a=team) | Match.objects.filter(team_b=team, status=MATCH_FINISHED)
    ).count()

    captain_full = f"{team.cap_name} {team.cap_surname}"

    team_roster = []
    for rs in roster_stats:
        pw = _points_won(rs["total_kills"] or 0, rs["total_aces"] or 0, rs["total_blocks"] or 0)

        name = f"{rs['player__first_name']} {rs['player__last_name']}"
        team_roster.append({
            "number": rs["jersey_number"],
            "name": name,
            "player_id": rs["player_id"],
            "position": rs["position"],
            "kills": rs["total_kills"] or 0,
            "points_won": pw,
            "attack_errors": rs["total_attack_errors"] or 0,
            "serve_attempts": rs["total_serve_attempts"] or 0,
            "serve_errors": rs["total_serve_errors"] or 0,
            "pass_errors": rs["total_pass_errors"] or 0,
            "setting_errors": rs["total_setting_errors"] or 0,
            "aces": rs["total_aces"] or 0,
            "blocks": rs["total_blocks"] or 0,
            "assists": rs["total_assists"] or 0,
            "is_captain": name == captain_full,
            "image": _resolve_photo(rs.get("player__photo_path", "")),
        })

    # Fallback: show roster from Player model when no match stats exist
    if not team_roster:
        for p in team.players.all().order_by("pk"):
            name = f"{p.first_name} {p.last_name}"
            team_roster.append({
                "number": p.jersey_number,
                "name": name,
                "player_id": p.pk,
                "position": p.position,
                "kills": 0, "points_won": 0,
                "attack_errors": 0,
                "serve_attempts": 0, "serve_errors": 0,
                "pass_errors": 0,
                "setting_errors": 0,
                "aces": 0, "blocks": 0, "assists": 0,
                "is_captain": name == captain_full,
                "image": _resolve_photo(p.photo_path),
            })

    totals = _aggregate_players(team_roster) if team_roster else {}

    # Match history
    team_matches_qs = (
        Match.objects
        .filter(team_a=team) | Match.objects.filter(team_b=team)
    )
    team_matches_qs = team_matches_qs.filter(status=MATCH_FINISHED).select_related("team_a", "team_b").order_by("start_time")

    team_matches = []
    wins = 0
    losses = 0
    total_sets_won = 0
    total_sets_lost = 0
    for m in team_matches_qs:
        is_home = (m.team_a_id == team.pk)
        opp = m.team_b if is_home else m.team_a
        score = f"{m.score_a}:{m.score_b}" if is_home else f"{m.score_b}:{m.score_a}"
        my_sets = m.score_a if is_home else m.score_b
        opp_sets = m.score_b if is_home else m.score_a
        total_sets_won += my_sets
        total_sets_lost += opp_sets

        if my_sets > opp_sets:
            wins += 1
            if m.stage == STAGE_GROUP:
                pts = 3 if opp_sets == 0 else 2
            else:
                pts = _stage_label(m.stage, m.group)
        else:
            losses += 1
            if m.stage == STAGE_GROUP:
                pts = 1 if my_sets == 1 else 0
            else:
                pts = _stage_label(m.stage, m.group)

        won = my_sets > opp_sets
        status_str = f"{pts} pts" if isinstance(pts, int) else pts
        opp_logo = ""
        opp_short = ""
        if opp:
            opp_logo = opp.logo_path or ""
            opp_short = opp.name[:2].upper()
        team_matches.append({
            "stage": _stage_label(m.stage, m.group),
            "opponent": opp.name if opp else "TBD",
            "opponent_logo": opp_logo,
            "opponent_short": opp_short,
            "result": score,
            "result_class": "win" if won else "loss",
            "status": status_str,
            "match_id": m.pk,
        })

    standing = GroupStanding.objects.filter(team=team).first()
    group_points = standing.points if standing else 0

    team_profile = {
        "name": team.name,
        "short": team.name[:2].upper(),
        "group": team.group_name or "-",
        "record": f"{wins}-{losses}",
        "seed": f"{team.group_name or '?'}{standing.rank_in_group if standing else '?'}",
        "league_level": team.get_league_level_display(),
        "captain": captain_full,
        "logo": team.logo_path or "",
        "image": team.logo_path or _DEFAULT_TEAM_IMAGE,
        "group_points": group_points,
        "set_ratio": _sets_label(total_sets_won, total_sets_lost),
        "points_won": totals.get("points_won", 0),
    }

    team_meta = [
        {"label_key": "team_page.meta_group", "label": "Group", "value": team_profile["group"]},
        {"label_key": "team_page.meta_record", "label": "Record", "value": team_profile["record"]},
        {"label_key": "team_page.meta_seed", "label": "Seed", "value": team_profile["seed"]},
        {"label_key": "team_page.meta_captain", "label": "Captain", "value": team_profile["captain"]},
        {"label_key": "team_page.meta_set_ratio", "label": "Set Ratio", "value": team_profile["set_ratio"]},
        {"label_key": "team_page.meta_group_pts", "label": "Group Pts", "value": team_profile["group_points"]},
    ]

    team_summary_cards = [
        {"label_key": "team_page.stat_record", "label": "Record (W-L)", "value": team_profile["record"]},
        {"label_key": "team_page.stat_kills", "label": "Total Kills", "value": totals.get("kills", 0)},
        {"label_key": "team_page.stat_aces", "label": "Total Aces", "value": totals.get("aces", 0)},
        {"label_key": "team_page.stat_blocks", "label": "Total Blocks", "value": totals.get("blocks", 0)},
        {"label_key": "team_page.stat_points", "label": "Points Won", "value": totals.get("points_won", 0)},
        {"label_key": "team_page.stat_assists", "label": "Total Assists", "value": totals.get("assists", 0)},
    ]

    team_breakdown_bars = [
        {"label_key": "tp.bar_points", "label": "Points Won", "value": totals.get("points_won", 0), "tone": "net"},
        {"label_key": "tp.bar_kills", "label": "Kills", "value": totals.get("kills", 0), "tone": "net"},
        {"label_key": "tp.bar_aces", "label": "Aces", "value": totals.get("aces", 0), "tone": "serve"},
        {"label_key": "tp.bar_blocks", "label": "Blocks", "value": totals.get("blocks", 0), "tone": "serve"},
    ]
    max_bar_value = max((item["value"] for item in team_breakdown_bars), default=1) or 1
    for item in team_breakdown_bars:
        item["percentage"] = round((item["value"] / max_bar_value) * 100, 1)

    # ── Form strip: last 5 match results as W/L dots ──
    form_strip = [
        {
            "result": "W" if mi["result_class"] == "win" else "L",
            "opponent_short": mi["opponent_short"],
            "score": mi["result"],
            "match_id": mi["match_id"],
        }
        for mi in team_matches[-5:]
    ]

    # ── Team leaders: top player per category ──
    def _pick_leader(roster, key, label):
        if not roster:
            return None
        best = max(roster, key=lambda p: p.get(key, 0))
        if best.get(key, 0) == 0:
            return None
        return {
            "category": label,
            "name": best["name"],
            "value": best[key],
            "player_id": best["player_id"],
            "image": best["image"],
        }

    team_leaders = [
        ldr for ldr in [
            _pick_leader(team_roster, "points_won", "Points"),
            _pick_leader(team_roster, "aces", "Aces"),
            _pick_leader(team_roster, "blocks", "Blocks"),
            _pick_leader(team_roster, "assists", "Assists"),
        ] if ldr is not None
    ]

    # ── Identity stats: 4 editorial metric bands ──
    serve_att = totals.get("serve_attempts", 0)
    serve_pressure_val = None
    if serve_att:
        serve_pressure_val = ((totals.get("aces", 0) - totals.get("serve_errors", 0)) / serve_att) * 100

    identity_stats = [
        {
            "key": "attack",
            "label": "Kill Power",
            "label_key": "tp.id_attack_label",
            "copy_key": "tp.id_attack_copy",
            "value": str(totals.get("kills", 0)),
            "raw": totals.get("kills", 0),
            "copy": "Total kills scored across all matches.",
        },
        {
            "key": "serve",
            "label": "Serve Pressure",
            "label_key": "tp.id_serve_label",
            "copy_key": "tp.id_serve_copy",
            "value": _pct_label(serve_pressure_val),
            "raw": serve_pressure_val or 0,
            "copy": "Ace rate minus serve errors as a share of total attempts.",
        },
        {
            "key": "block",
            "label": "Block Presence",
            "label_key": "tp.id_block_label",
            "copy_key": "tp.id_block_copy",
            "value": str(totals.get("blocks", 0)),
            "raw": totals.get("blocks", 0),
            "copy": "Total blocks won across all matches.",
        },
        {
            "key": "reception",
            "label": "Assist Output",
            "label_key": "tp.id_reception_label",
            "copy_key": "tp.id_reception_copy",
            "value": str(totals.get("assists", 0)),
            "raw": totals.get("assists", 0),
            "copy": "Total assists delivered across all matches.",
        },
    ]

    return {
        "team_profile": team_profile,
        "team_meta": team_meta,
        "team_summary_cards": team_summary_cards,
        "team_breakdown_bars": team_breakdown_bars,
        "team_roster": team_roster,
        "team_matches": team_matches,
        "form_strip": form_strip,
        "team_leaders": team_leaders,
        "identity_stats": identity_stats,
    }


def get_player_detail(player_id: int) -> dict | None:
    """Full context dict for the player detail page."""
    try:
        player = Player.objects.select_related("team").get(pk=player_id)
    except Player.DoesNotExist:
        return None

    match_stats = (
        PlayerMatchStats.objects
        .filter(player=player)
        .select_related("match", "match__team_a", "match__team_b")
        .order_by("match__start_time")
    )

    match_log = []
    cumulative = {
        "kills": 0, "aces": 0, "blocks": 0,
        "attack_errors": 0,
        "serve_attempts": 0,
        "pass_errors": 0,
        "assists": 0, "sets_played": 0,
    }
    position = ""

    for ps in match_stats:
        m = ps.match
        is_home = (m.team_a_id == ps.team_id)
        opp = m.team_b if is_home else m.team_a
        position = ps.position

        pw = _points_won(ps.kills, ps.aces, ps.blocks)

        match_log.append({
            "stage": _stage_label(m.stage, m.group),
            "date": m.start_time.strftime("%d %b"),
            "opponent": opp.name if opp else "TBD",
            "kills": ps.kills,
            "points_won": pw,
            "aces": ps.aces,
            "blocks": ps.blocks,
            "sets_played": ps.sets_played,
            "match_id": m.pk,
        })

        for k in cumulative:
            cumulative[k] += getattr(ps, k, 0)

    total_pw = _points_won(cumulative["kills"], cumulative["aces"], cumulative["blocks"])
    total_ace = _safe_pct(cumulative["aces"], cumulative["serve_attempts"])

    # TOTAL / AVERAGE row
    n_matches = len(match_log) or 1
    totals_row = {
        "stage": "TOTAL",
        "date": "",
        "opponent": f"{len(match_log)} matches",
        "kills": cumulative["kills"],
        "points_won": total_pw,
        "aces": cumulative["aces"],
        "blocks": cumulative["blocks"],
        "match_id": None,
        "is_total": True,
    }

    pos_display = dict(
        OH="Outside Hitter", MB="Middle Blocker", S="Setter",
        OPP="Opposite", L="Libero",
    ).get(position, position)

    # ── Rank calculation ──
    ranks = _compute_player_ranks(player_id, cumulative)

    # Awards: MVP selections + Dream Team entries
    awards = []
    for sel in MVPSelection.objects.filter(player=player):
        awards.append({"type": "mvp", "label": sel.reason or sel.get_mvp_type_display()})
    for dte in DreamTeamEntry.objects.filter(player=player):
        awards.append({"type": "dream_team", "label": f"Dream Team — {dte.position}"})
    # Category leader positions from ranks
    for cat in ranks:
        if ranks[cat]["rank"] == 1:
            awards.append({"type": "leader", "label": f"#{1} {cat.replace('_', ' ').title()}"})

    player_profile = {
        "name": f"{player.first_name} {player.last_name}",
        "team": player.team.name,
        "team_id": player.team_id,
        "team_logo": player.team.logo_path or "",
        "position": pos_display,
        "position_short": position,
        "number": player.jersey_number or 0,
        "matches_played": len(match_log),
        "image": player.photo_path or "",
        "awards": awards,
    }

    player_meta = [
        {"label_key": "player_page.meta_team", "label": "Team", "value": player.team.name, "url_team_id": player.team_id},
        {"label_key": "player_page.meta_position", "label": "Position", "value": pos_display},
        {"label_key": "player_page.meta_number", "label": "Number", "value": f"#{player.jersey_number or '-'}"},
        {"label_key": "player_page.meta_matches", "label": "Matches", "value": len(match_log)},
    ]

    player_summary_cards = [
        {"label_key": "player_page.stat_points_won", "label": "Points Won", "value": total_pw, "rank": ranks.get("points_won")},
        {"label_key": "player_page.stat_kills", "label": "Kills", "value": cumulative["kills"], "rank": ranks.get("kills")},
        {"label_key": "player_page.stat_aces", "label": "Aces", "value": cumulative["aces"], "rank": ranks.get("aces")},
        {"label_key": "player_page.stat_blocks", "label": "Blocks", "value": cumulative["blocks"], "rank": ranks.get("blocks")},
        {"label_key": "player_page.stat_assists", "label": "Assists", "value": cumulative["assists"], "rank": ranks.get("assists")},
    ]

    player_hero_stats = [
        {"label": "Matches", "label_key": "player_page.hero_matches", "value": len(match_log)},
        {"label": "Points", "label_key": "player_page.hero_points", "value": total_pw},
        {"label": "Kills", "label_key": "player_page.hero_kills", "value": cumulative["kills"]},
        {"label": "Aces", "label_key": "player_page.hero_aces", "value": cumulative["aces"]},
        {"label": "Blocks", "label_key": "player_page.hero_blocks", "value": cumulative["blocks"]},
    ]

    # ── Position Fingerprint ── role-based stat emphasis ──
    _fingerprint_map = {
        "S": [
            ("Assists", cumulative.get("assists", 0)),
            ("Serve Pressure", _pct_label(total_ace)),
            ("Points Won", total_pw),
        ],
        "MB": [
            ("Blocks", cumulative["blocks"]),
            ("Kills", cumulative["kills"]),
            ("Points Won", total_pw),
        ],
        "L": [
            ("Sets Played", cumulative["sets_played"]),
            ("Pass Errors", cumulative["pass_errors"]),
            ("Assists", cumulative.get("assists", 0)),
        ],
    }
    # OH, OPP and default share the same emphasis
    _default_fp = [
        ("Kills", cumulative["kills"]),
        ("Aces", cumulative["aces"]),
        ("Points Won", total_pw),
    ]
    fingerprint_raw = _fingerprint_map.get(position, _default_fp)
    position_fingerprint = [{"label": fp[0], "value": fp[1]} for fp in fingerprint_raw]

    # ── Form strip — last 5 match results ──
    form_strip = []
    for ml in match_log[-5:]:
        form_strip.append({
            "opponent": ml["opponent"],
            "stage": ml["stage"],
            "match_id": ml["match_id"],
            "points_won": ml["points_won"],
        })

    # ── Role statement — narrative hook ──
    role_statement = None
    for cat in ranks:
        if ranks[cat]["rank"] == 1:
            role_statement = f"Tournament's #{1} in {cat.replace('_', ' ').title()}"
            break
    if not role_statement and ranks:
        best = min(ranks.items(), key=lambda x: x[1]["rank"])
        if best[1]["rank"] <= 3:
            ordinal = {1: "1st", 2: "2nd", 3: "3rd"}.get(best[1]["rank"], f"{best[1]['rank']}th")
            role_statement = f"{ordinal} in {best[0].replace('_', ' ').title()}"

    # ── Player radar stats (4-axis, same shape as team) ──
    p_serve_att = cumulative.get("serve_attempts", 0)
    p_serve_pressure = None
    if p_serve_att:
        p_serve_pressure = ((cumulative["aces"] - cumulative.get("serve_errors", 0)) / p_serve_att) * 100

    player_radar_stats = [
        {"key": "attack", "label": "Attack", "value": str(cumulative["kills"]), "raw": cumulative["kills"]},
        {"key": "serve", "label": "Serve", "value": _pct_label(p_serve_pressure), "raw": p_serve_pressure or 0},
        {"key": "block", "label": "Block", "value": str(cumulative["blocks"]), "raw": cumulative["blocks"]},
        {"key": "reception", "label": "Reception", "value": str(cumulative["assists"]), "raw": cumulative["assists"]},
    ]

    return {
        "player_profile": player_profile,
        "player_meta": player_meta,
        "player_hero_stats": player_hero_stats,
        "player_summary_cards": player_summary_cards,
        "player_match_log": match_log,
        "player_totals_row": totals_row,
        "position_fingerprint": position_fingerprint,
        "form_strip": form_strip,
        "role_statement": role_statement,
        "player_radar_stats": player_radar_stats,
    }


def _compute_player_ranks(player_id: int, cumulative: dict) -> dict:
    """
    Compute rank of a player in each stat category among all tournament players.
    Returns dict of category → {value, rank, total}.
    """
    # Aggregate all players' totals
    all_players = (
        PlayerMatchStats.objects
        .values("player_id")
        .annotate(
            total_kills=Sum("kills"),
            total_aces=Sum("aces"),
            total_blocks=Sum("blocks"),
            total_assists=Sum("assists"),
        )
    )

    # Build sorted lists for each category
    player_totals = []
    for p in all_players:
        kills = p["total_kills"] or 0
        aces = p["total_aces"] or 0
        blocks = p["total_blocks"] or 0
        pw = _points_won(kills, aces, blocks)
        player_totals.append({
            "player_id": p["player_id"],
            "points_won": pw,
            "kills": kills,
            "aces": aces,
            "blocks": blocks,
            "assists": p["total_assists"] or 0,
        })

    total_players = len(player_totals)
    categories = ["points_won", "kills", "aces", "blocks", "assists"]
    my_values = {
        "points_won": _points_won(cumulative["kills"], cumulative["aces"], cumulative["blocks"]),
        "kills": cumulative["kills"],
        "aces": cumulative["aces"],
        "blocks": cumulative["blocks"],
        "assists": cumulative.get("assists", 0),
    }

    ranks = {}
    for cat in categories:
        sorted_list = sorted(player_totals, key=lambda x: x[cat], reverse=True)
        rank = 1
        for i, entry in enumerate(sorted_list):
            if entry["player_id"] == player_id:
                rank = i + 1
                break
        ranks[cat] = {"value": my_values[cat], "rank": rank, "total": total_players}

    return ranks


def get_dream_team() -> list[dict]:
    """
    Dream team entries for the court visualization.

    Returns list of ``{slot, position, number, name, team, metric, player_id}``.
    """
    entries = DreamTeamEntry.objects.select_related("player", "team").order_by("slot")
    return [
        {
            "slot": e.slot,
            "position": e.position,
            "number": e.player.jersey_number or 0,
            "name": f"{e.player.first_name} {e.player.last_name}",
            "team": e.team.name,
            "team_id": e.team_id,
            "team_logo": e.team.logo_path or "",
            "metric": e.metric_label,
            "player_id": e.player_id,
            "image": _resolve_photo(e.player.photo_path),
        }
        for e in entries
    ]


def get_category_leaders() -> list[dict]:
    """
    Top player in each statistical category across the tournament.

    Returns list of ``{category, label, player_name, team, value, player_id}``.
    """
    MIN_SERVE_ATTEMPTS = 5

    all_players = (
        PlayerMatchStats.objects
        .values("player_id", "player__first_name", "player__last_name", "player__photo_path", "team_id", "team__name", "team__logo_path")
        .annotate(
            total_kills=Sum("kills"),
            total_aces=Sum("aces"),
            total_blocks=Sum("blocks"),
            total_assists=Sum("assists"),
            total_serve_attempts=Sum("serve_attempts"),
        )
    )

    leaders = []
    categories = [
        ("top_scorer", "Top Scorer", "points_won"),
        ("best_server", "Best Server", "ace_pct"),
        ("best_blocker", "Best Blocker", "blocks"),
        ("best_setter", "Best Setter", "assists"),
    ]

    player_list = []
    for p in all_players:
        kills = p["total_kills"] or 0
        aces = p["total_aces"] or 0
        blocks = p["total_blocks"] or 0
        assists = p["total_assists"] or 0
        sa = p["total_serve_attempts"] or 0

        player_list.append({
            "player_id": p["player_id"],
            "name": f"{p['player__first_name']} {p['player__last_name']}",
            "image": _resolve_photo(p.get("player__photo_path", "")),
            "team": p["team__name"],
            "team_id": p.get("team_id"),
            "team_logo": p.get("team__logo_path") or "",
            "points_won": _points_won(kills, aces, blocks),
            "ace_pct": _safe_pct(aces, sa) if sa >= MIN_SERVE_ATTEMPTS else None,
            "blocks": blocks,
            "assists": assists,
        })

    for cat_key, cat_label, stat_key in categories:
        eligible = [p for p in player_list if p[stat_key] is not None]
        if not eligible:
            continue
        best = max(eligible, key=lambda x: x[stat_key])
        val = best[stat_key]
        if stat_key == "ace_pct":
            display = f"{val:.1f}%"
        else:
            display = str(val)
        leaders.append({
            "category": cat_key,
            "label": cat_label,
            "player_name": best["name"],
            "image": best["image"],
            "team": best["team"],
            "team_id": best.get("team_id"),
            "team_logo": best.get("team_logo", ""),
            "value": display,
            "player_id": best["player_id"],
        })

    return leaders


def get_highlights() -> list[dict]:
    """Recent highlights for the tournament hub."""
    qs = MatchHighlight.objects.select_related("match").order_by("order")[:10]
    return [
        {
            "title": h.title,
            "copy": h.description[:100] if h.description else "",
            "match": _stage_label(h.match.stage, h.match.group) if h.match else "Tournament",
            "duration": "",
            "match_id": h.match_id,
        }
        for h in qs
    ]


def get_mvp(mvp_type: str = MVP_MATCH) -> dict | None:
    """Single MVP selection by type."""
    sel = (
        MVPSelection.objects
        .filter(mvp_type=mvp_type)
        .select_related("player", "team")
        .first()
    )
    if not sel:
        return None
    return {
        "name": f"{sel.player.first_name} {sel.player.last_name}",
        "team": sel.team.name,
        "team_logo": sel.team.logo_path or "",
        "image": _resolve_photo(sel.player.photo_path),
        "reason": sel.reason,
    }
