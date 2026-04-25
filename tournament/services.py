"""
Business-logic layer for tournament registration and stats import.

Keeps views thin by encapsulating creation / parsing
logic in pure-Python functions that are easy to test.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.db.models import Sum, F, Q
from django.utils import timezone

from .constants import (
    MAX_TOURNAMENT_SLOTS,
    MATCH_FINISHED,
    MATCH_SCHEDULED,
    MVP_WEIGHTS,
    PAYMENT_ACCEPTED,
    PAYMENT_WAITING,
    POSITION_L,
    POSITION_MB,
    POSITION_OH,
    POSITION_OPP,
    POSITION_S,
    STAGE_GROUP,
)
from .models import (
    DreamTeamEntry,
    GameSet,
    GroupStanding,
    Match,
    Player,
    PlayerMatchStats,
    Team,
    TeamMatchStats,
)

logger = logging.getLogger(__name__)


# ── Public API ───────────────────────────────────────────

def get_available_slots() -> int:
    """Return remaining open slots based on accepted teams."""
    approved = Team.objects.filter(payment_status=PAYMENT_ACCEPTED).count()
    return max(MAX_TOURNAMENT_SLOTS - approved, 0)


@transaction.atomic
def register_team(cleaned: dict, players_data: list[dict] | None = None) -> Team:
    """
    Create a Team (+ Players) from validated form data.

    Parameters
    ----------
    cleaned : dict
        Output of ``TeamRegistrationForm.cleaned_data``.
    players_data : list[dict] | None
        List of player dicts from the request (validated outside the form).

    Returns
    -------
    Team
        The newly created Team instance.

    Raises
    ------
    ValueError
        If team name or email is already taken.
    """
    team_name = cleaned["teamName"]
    email = cleaned["email"]
    cap = cleaned["capName"]  # dict with 'first' / 'last'

    if Team.objects.filter(name=team_name).exists():
        raise ValueError("Team name already taken.")

    if Team.objects.filter(cap_email=email).exists():
        raise ValueError("This email is already registered.")

    phone = cleaned.get("phone") or None
    if phone and Team.objects.filter(cap_phone=phone).exists():
        raise ValueError("This phone number is already registered.")

    team = Team.objects.create(
        name=team_name,
        cap_name=cap["first"],
        cap_surname=cap["last"],
        cap_phone=phone,
        cap_email=email,
        payment_status=PAYMENT_WAITING,
        entrance_url=cleaned.get("entranceUrl") or None,
        entrance_title=cleaned.get("entranceTitle") or None,
        entrance_artist=cleaned.get("entranceArtist") or None,
        entrance_artwork_url=cleaned.get("entranceArtworkUrl") or None,
        entrance_source=cleaned.get("entranceSource") or "soundcloud",
        entrance_start_seconds=cleaned.get("entranceStartSeconds") or 0,
    )

    if players_data:
        _create_players(team, players_data)

    return team


# ── Private Helpers ──────────────────────────────────────

def _create_players(team: Team, players_data: list[dict]) -> None:
    """
    Bulk-create Player rows from a list of validated player dicts.

    Each dict is expected to have keys: firstName and lastName.
    """
    from .forms import PlayerForm

    players_to_create: list[Player] = []
    for entry in players_data:
        form = PlayerForm(entry)
        if not form.is_valid():
            continue  # skip malformed entries rather than hard-fail

        cd = form.cleaned_data
        first = cd.get("firstName", "").strip()
        if not first:
            continue

        players_to_create.append(
            Player(
                team=team,
                first_name=first,
                last_name=cd.get("lastName", "").strip(),

            )
        )

    if players_to_create:
        Player.objects.bulk_create(players_to_create)


# ── Schedule CSV Import ──────────────────────────────────


def parse_schedule_csv(file_obj) -> dict:
    """
    Parse a schedule CSV file and validate rows.

    Expected columns (case-insensitive, order doesn't matter):
      Time, Team A, Team B, Group, Court, Stage (optional, defaults to GROUP)

    Accepts comma or semicolon delimiters.
    Returns dict with ``rows``, ``errors``.
    """
    import csv
    import io
    from datetime import datetime

    raw = file_obj.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig")

    # Detect delimiter
    delimiter = ";" if ";" in raw.split("\n")[0] else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=delimiter)

    # Normalise header names
    if reader.fieldnames is None:
        return {"rows": [], "errors": ["Empty CSV file."]}

    header_map = {}
    for h in reader.fieldnames:
        key = h.strip().lower().replace(" ", "_")
        header_map[h] = key

    rows = []
    errors = []
    team_cache: dict[str, int | None] = {}

    def lookup_team(name: str) -> int | None:
        name = name.strip()
        if not name:
            return None
        if name not in team_cache:
            try:
                team_cache[name] = Team.objects.get(name__iexact=name).pk
            except Team.DoesNotExist:
                team_cache[name] = None
        return team_cache[name]

    for i, raw_row in enumerate(reader, start=2):
        row = {header_map.get(k, k): v.strip() if v else "" for k, v in raw_row.items()}

        # Time (required)
        time_str = row.get("time", "")
        parsed_time = None
        for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M",
                     "%Y-%m-%dT%H:%M", "%d.%m.%Y %H:%M:%S"):
            try:
                parsed_time = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
        if not parsed_time:
            errors.append(f"Row {i}: invalid time '{time_str}'.")
            continue

        # Court (required)
        court_str = row.get("court", "")
        try:
            court = int(court_str)
            if court not in (1, 2, 3):
                raise ValueError
        except (ValueError, TypeError):
            errors.append(f"Row {i}: invalid court '{court_str}' (must be 1, 2 or 3).")
            continue

        # Stage (optional, default GROUP)
        stage = row.get("stage", "").upper() or STAGE_GROUP
        stage_valid = {c[0] for c in Match._meta.get_field("stage").choices}
        if stage not in stage_valid:
            errors.append(f"Row {i}: invalid stage '{stage}'.")
            continue

        group = row.get("group", "").upper()

        # Teams
        team_a_name = row.get("team_a", "")
        team_b_name = row.get("team_b", "")
        team_a_id = lookup_team(team_a_name)
        team_b_id = lookup_team(team_b_name)

        row_errors = []
        if team_a_name and team_a_id is None:
            row_errors.append(f"Team A '{team_a_name}' not found")
        if team_b_name and team_b_id is None:
            row_errors.append(f"Team B '{team_b_name}' not found")
        if team_a_id and team_b_id and team_a_id == team_b_id:
            row_errors.append("Team A and Team B are the same")

        if row_errors:
            errors.append(f"Row {i}: {'; '.join(row_errors)}.")
            continue

        rows.append({
            "row_num": i,
            "time": parsed_time,
            "court": court,
            "stage": stage,
            "group": group,
            "team_a_id": team_a_id,
            "team_a_name": team_a_name or "TBD",
            "team_b_id": team_b_id,
            "team_b_name": team_b_name or "TBD",
        })

    # Check for court/time conflicts within the CSV itself
    seen: dict[tuple, int] = {}
    for r in rows:
        key = (r["time"], r["court"])
        if key in seen:
            errors.append(
                f"Row {r['row_num']}: duplicate court/time slot "
                f"(conflicts with row {seen[key]})."
            )
        else:
            seen[key] = r["row_num"]

    # Check for court/time conflicts against existing DB matches
    for r in rows:
        if Match.objects.filter(court=r["court"], start_time=r["time"]).exists():
            errors.append(
                f"Row {r['row_num']}: Court {r['court']} at "
                f"{r['time']:%d %b %H:%M} is already booked."
            )

    return {"rows": rows, "errors": errors}


@transaction.atomic
def import_schedule_csv(rows: list[dict]) -> int:
    """
    Create Match objects from parsed schedule rows.

    Auto-assigns match_number sequentially.
    Returns count of created matches.
    """
    max_num = (
        Match.objects.order_by("-match_number")
        .values_list("match_number", flat=True)
        .first()
        or 0
    )

    matches = []
    for i, r in enumerate(rows, start=1):
        matches.append(
            Match(
                match_number=max_num + i,
                stage=r["stage"],
                group=r["group"],
                court=r["court"],
                start_time=r["time"],
                team_a_id=r["team_a_id"],
                team_b_id=r["team_b_id"],
                status=MATCH_SCHEDULED,
            )
        )

    Match.objects.bulk_create(matches)
    logger.info("Schedule CSV imported: %d matches created", len(matches))
    return len(matches)


# ── Stats Import (CSV / XML) ─────────────────────────────


def _detect_format(raw: str) -> str:
    """Return 'xml' if content looks like XML, else 'csv'."""
    stripped = raw.lstrip()
    if stripped.startswith("<") or stripped.startswith("<?xml"):
        return "xml"
    return "csv"


def preview_stats_import(file_obj, match_id: int, team_id: int | None = None) -> dict:
    """
    Parse CSV or XML and validate against DB without writing anything.

    Returns dict with ``preview``, ``errors``, ``warnings``, ``can_import``, ``format``.
    """
    from .csv_import import parse_csv, validate_against_db
    from .xml_import import parse_xml

    # Read raw content to detect format
    if hasattr(file_obj, "read"):
        raw = file_obj.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig")
    else:
        raw = str(file_obj)

    fmt = _detect_format(raw)

    import io
    if fmt == "xml":
        parsed = parse_xml(io.StringIO(raw))
    else:
        parsed = parse_csv(io.StringIO(raw))

    if parsed["errors"]:
        return {
            "preview": [],
            "errors": parsed["errors"],
            "warnings": parsed["warnings"],
            "can_import": False,
            "format": fmt,
        }

    validated = validate_against_db(parsed["rows"], match_id, team_id)
    all_errors = parsed["errors"] + validated["errors"]
    all_warnings = parsed["warnings"]

    if validated["unmatched_players"]:
        for u in validated["unmatched_players"]:
            all_warnings.append(
                f"Player '{u.get('player_name')}' (#{u.get('jersey_number')}) "
                f"not found in roster — will be skipped."
            )

    can_import = len(validated["valid_rows"]) > 0 and not all_errors

    return {
        "preview": validated["valid_rows"],
        "errors": all_errors,
        "warnings": all_warnings,
        "can_import": can_import,
        "format": fmt,
    }


# Keep old name as alias for backwards compat
def preview_csv_import(file_obj, match_id: int, team_id: int | None = None) -> dict:
    return preview_stats_import(file_obj, match_id, team_id)


@transaction.atomic
def confirm_stats_import(
    file_obj, match_id: int, team_id: int | None = None,
) -> dict:
    """
    Import player stats from CSV or XML into the database.

    When *team_id* is given only that team's stats are replaced;
    otherwise all stats for the match are wiped (legacy mode).
    """
    result = preview_stats_import(file_obj, match_id, team_id)
    if not result["can_import"]:
        raise ValueError(
            "Cannot import: " + "; ".join(result["errors"] or ["no valid rows"])
        )

    match = Match.objects.select_related("team_a", "team_b").get(pk=match_id)

    if team_id:
        # Team-scoped: only wipe this team's data
        PlayerMatchStats.objects.filter(match=match, team_id=team_id).delete()
        TeamMatchStats.objects.filter(match=match, team_id=team_id).delete()
    else:
        # Full wipe (legacy)
        PlayerMatchStats.objects.filter(match=match).delete()
        TeamMatchStats.objects.filter(match=match).delete()
        GameSet.objects.filter(match=match).delete()

    # Fallback sets_played: total sets in the match (score_a + score_b)
    fallback_sets = (match.score_a or 0) + (match.score_b or 0)

    # Create PlayerMatchStats
    stats_objects = []
    for row in result["preview"]:
        # Use per-player sets_played from XML if available, else fallback
        sp = row.get("sets_played", 0)
        if not sp and fallback_sets:
            sp = fallback_sets

        stats_objects.append(
            PlayerMatchStats(
                match=match,
                player_id=row["_player_id"],
                team_id=row["_team_id"],
                position=row.get("position", ""),
                jersey_number=row.get("jersey_number", 0),
                serve_attempts=row.get("serve_attempts", 0),
                aces=row.get("aces", 0),
                serve_errors=row.get("serve_errors", 0),
                kills=row.get("kills", 0),
                attack_errors=row.get("attack_errors", 0),
                pass_errors=row.get("pass_errors", 0),
                blocks=row.get("blocks", 0),
                assists=row.get("assists", 0),
                setting_errors=row.get("setting_errors", 0),
                sets_played=sp,
            )
        )
    PlayerMatchStats.objects.bulk_create(stats_objects)

    # Aggregate TeamMatchStats
    only_team = Team.objects.get(pk=team_id) if team_id else None
    _aggregate_team_stats(match, only_team=only_team)

    # Determine if match is fully imported (both teams have stats)
    if team_id:
        both = all(
            PlayerMatchStats.objects.filter(match=match, team=t).exists()
            for t in filter(None, [match.team_a, match.team_b])
        )
        if both:
            match.status = MATCH_FINISHED
            match.stats_imported = True
            match.stats_imported_at = timezone.now()
            match.save(update_fields=["status", "stats_imported", "stats_imported_at"])
            if match.stage == STAGE_GROUP:
                recalculate_standings()
    else:
        match.status = MATCH_FINISHED
        match.stats_imported = True
        match.stats_imported_at = timezone.now()
        match.save(update_fields=["status", "stats_imported", "stats_imported_at"])
        if match.stage == STAGE_GROUP:
            recalculate_standings()

    recalculate_dream_team()

    logger.info("Stats import complete for match M%s: %d rows", match.match_number, len(stats_objects))

    return {"imported": len(stats_objects), "warnings": result["warnings"]}


# Keep old name as alias for backwards compat
def confirm_csv_import(file_obj, match_id: int, team_id: int | None = None) -> dict:
    return confirm_stats_import(file_obj, match_id, team_id)


def _aggregate_team_stats(match: Match, only_team=None) -> None:
    """Sum player stats into TeamMatchStats for each team in a match."""
    agg_fields = [
        "serve_attempts", "aces", "serve_errors",
        "kills", "attack_errors",
        "pass_errors",
        "blocks",
    ]
    if only_team:
        teams = [only_team]
    else:
        teams = list(filter(None, [match.team_a, match.team_b]))
    for team in teams:
        agg = PlayerMatchStats.objects.filter(
            match=match, team=team
        ).aggregate(**{f: Sum(f) for f in agg_fields})
        TeamMatchStats.objects.create(
            match=match,
            team=team,
            **{f: agg[f] or 0 for f in agg_fields},
        )


# ── Recalculation ────────────────────────────────────────


def recalculate_standings() -> None:
    """
    Rebuild every GroupStanding row from finished GROUP matches.

    Scoring: 2-0 win → 3 pts, 2-1 win → 2 pts, 1-2 loss → 1 pt, 0-2 loss → 0 pts.
    Rank within group by: points → wins → set ratio.
    """
    group_matches = Match.objects.filter(
        stage=STAGE_GROUP, status=MATCH_FINISHED,
    ).select_related("team_a", "team_b")

    # Collect per-team accumulators
    team_data: dict[int, dict] = {}

    # Ensure ALL grouped teams are present (not just those with existing standings)
    for team in Team.objects.filter(group_name__isnull=False).exclude(group_name=""):
        team_data[team.pk] = {
            "group": team.group_name,
            "played": 0, "wins": 0, "losses": 0,
            "sets_won": 0, "sets_lost": 0, "points": 0,
        }

    # Also keep any existing standings data as seed (covers edge cases)
    for gs in GroupStanding.objects.select_related("team"):
        if gs.team_id not in team_data:
            team_data[gs.team_id] = {
                "group": gs.group,
                "played": 0, "wins": 0, "losses": 0,
                "sets_won": 0, "sets_lost": 0, "points": 0,
            }

    for m in group_matches:
        for team, opp, score, opp_score in [
            (m.team_a, m.team_b, m.score_a, m.score_b),
            (m.team_b, m.team_a, m.score_b, m.score_a),
        ]:
            if team is None:
                continue
            if team.pk not in team_data:
                team_data[team.pk] = {
                    "group": team.group_name or "",
                    "played": 0, "wins": 0, "losses": 0,
                    "sets_won": 0, "sets_lost": 0, "points": 0,
                }
            d = team_data[team.pk]
            d["played"] += 1
            d["sets_won"] += score
            d["sets_lost"] += opp_score
            if score > opp_score:
                d["wins"] += 1
                d["points"] += 3 if opp_score == 0 else 2  # 2-0 → 3, 2-1 → 2
            else:
                d["losses"] += 1
                d["points"] += 1 if score == 1 else 0  # 1-2 → 1, 0-2 → 0

    # Rank within each group
    from collections import defaultdict
    groups: dict[str, list[int]] = defaultdict(list)
    for tid, d in team_data.items():
        groups[d["group"]].append(tid)

    for group_name, team_ids in groups.items():
        ranked = sorted(
            team_ids,
            key=lambda tid: (
                team_data[tid]["points"],
                team_data[tid]["wins"],
                (team_data[tid]["sets_won"] / team_data[tid]["sets_lost"])
                if team_data[tid]["sets_lost"] else float("inf"),
            ),
            reverse=True,
        )
        for rank, tid in enumerate(ranked, start=1):
            team_data[tid]["rank_in_group"] = rank

    # Write back
    for tid, d in team_data.items():
        GroupStanding.objects.update_or_create(
            team_id=tid,
            defaults={
                "group": d["group"],
                "played": d["played"],
                "wins": d["wins"],
                "losses": d["losses"],
                "sets_won": d["sets_won"],
                "sets_lost": d["sets_lost"],
                "points": d["points"],
                "rank_in_group": d.get("rank_in_group", 0),
            },
        )
    logger.info("Standings recalculated for %d teams", len(team_data))


def recalculate_dream_team() -> None:
    """
    Select 7 best players by position across all matches using weighted
    per-set MVP formulas.

    OH/OPP/MB/S → highest weighted score per set.
    L → closest to 0 (fewest pass errors per set) — inverted ranking.
    Produces 7 entries: OH×2, MB×2, OPP×1, S×1, L×1.
    """
    SLOT_MAP = {
        POSITION_OH: ["front-left", "back-right"],
        POSITION_MB: ["front-center", "back-center"],
        POSITION_OPP: ["front-right"],
        POSITION_S: ["back-left"],
        POSITION_L: ["libero"],
    }

    # Remove previous auto-calculated entries
    DreamTeamEntry.objects.filter(is_auto=True).delete()

    entries = []
    for pos, slots in SLOT_MAP.items():
        weights = MVP_WEIGHTS[pos]
        needed = len(slots)

        # Get all stat rows for this position
        qs = PlayerMatchStats.objects.filter(position=pos)

        # Aggregate per player: sum each stat field and total sets_played
        agg_fields = list({f for f, _ in weights}) + ["sets_played"]
        agg_kwargs = {f: Sum(f) for f in agg_fields}
        leaders_qs = (
            qs.values("player_id", "team_id")
            .annotate(**agg_kwargs)
        )

        scored: list[tuple[float, dict]] = []
        for row in leaders_qs:
            total_sets = row["sets_played"] or 0
            if total_sets == 0:
                continue  # can't compute per-set score

            # "Did they play?" filter:
            # S: skip if assists==0 AND setting_errors==0
            # L: skip if pass_errors==0
            # Others: skip if all weighted fields are 0
            if pos == POSITION_S:
                if (row.get("assists") or 0) == 0 and (row.get("setting_errors") or 0) == 0:
                    continue
            elif pos == POSITION_L:
                if (row.get("pass_errors") or 0) == 0:
                    continue
            else:
                if all((row.get(f) or 0) == 0 for f, _ in weights):
                    continue

            # Compute weighted score
            raw_score = sum(
                (row.get(field) or 0) * weight
                for field, weight in weights
            )
            per_set = raw_score / total_sets
            scored.append((per_set, row))

        # Sort: L → closest to 0 (ascending by abs), others → descending
        if pos == POSITION_L:
            scored.sort(key=lambda x: abs(x[0]))
        else:
            scored.sort(key=lambda x: x[0], reverse=True)

        for i, (score, row) in enumerate(scored[:needed]):
            try:
                player = Player.objects.get(pk=row["player_id"])
            except Player.DoesNotExist:
                continue
            total_sets = row["sets_played"] or 1
            entries.append(
                DreamTeamEntry(
                    position=pos,
                    slot=slots[i],
                    player=player,
                    team_id=row["team_id"],
                    metric_label=f"{score:+.2f} / set",
                    metric_value=float(score),
                    is_auto=True,
                )
            )

    DreamTeamEntry.objects.bulk_create(entries)
    logger.info("Dream Team recalculated: %d entries", len(entries))

