"""
CSV parser and database validator for SoloStats Live exports.

SoloStats Live dumps a *multi-section* CSV: several tables stacked
vertically in one file, separated by blank lines.  Each section has its
own header row.  This parser splits the file into sections, resolves
column aliases, and merges all sections by ``Player Number``.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from .constants import POSITION_CHOICES
from .csv_mapping import (
    COLUMN_ALIASES,
    CSV_TO_MODEL,
    REQUIRED_COLUMNS,
    SKIP_PLAYER_NUMBERS,
)

_VALID_POSITIONS = {code for code, _ in POSITION_CHOICES}


# ── Public API ───────────────────────────────────────────


def parse_csv(file_obj) -> dict[str, Any]:
    """
    Parse a (possibly multi-section) CSV into merged player-stat dicts.

    Returns dict with keys ``rows``, ``errors``, ``warnings``.
    """
    try:
        if hasattr(file_obj, "read"):
            raw = file_obj.read()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8-sig")
        else:
            raw = str(file_obj)
    except Exception as exc:
        return {"rows": [], "errors": [f"Cannot read CSV: {exc}"], "warnings": []}

    sections = _split_sections(raw)
    if not sections:
        return {"rows": [], "errors": ["CSV file is empty or has no header row."], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []

    # Merge all sections into {player_number: {field: value}}
    merged: dict[str, dict[str, Any]] = {}
    all_headers_seen: set[str] = set()

    for sec_idx, section_text in enumerate(sections, start=1):
        reader = csv.DictReader(io.StringIO(section_text))
        if reader.fieldnames is None:
            continue

        # Build header map with alias resolution
        header_map: dict[str, str] = {}
        for h in reader.fieldnames:
            stripped = h.strip()
            canonical = COLUMN_ALIASES.get(stripped, stripped)
            header_map[canonical] = h
            all_headers_seen.add(canonical)

        # This section must have Player Number (or Jersey alias)
        pn_header = header_map.get("Player Number")
        if pn_header is None:
            continue  # not a player-stats section, skip

        for line_no, raw_row in enumerate(reader, start=2):
            pn_val = (raw_row.get(pn_header) or "").strip()
            if not pn_val or pn_val.lower() in SKIP_PLAYER_NUMBERS:
                continue

            if pn_val not in merged:
                merged[pn_val] = {}

            row_data = merged[pn_val]
            row_errors, row_warnings = _extract_fields(
                raw_row, header_map, row_data, sec_idx, line_no
            )
            errors.extend(row_errors)
            warnings.extend(row_warnings)

    # Check required columns across all sections
    missing = REQUIRED_COLUMNS - all_headers_seen
    if missing:
        errors.append(f"Missing required columns: {', '.join(sorted(missing))}")
        return {"rows": [], "errors": errors, "warnings": warnings}

    if errors:
        return {"rows": [], "errors": errors, "warnings": warnings}

    # Convert merged dict → list of rows
    rows: list[dict] = []
    for pn, data in merged.items():
        if not pn.isdigit():
            errors.append(f"Player Number '{pn}' is not a valid number.")
            continue
        data["jersey_number"] = pn

        # player_name may be "(N/A)" in SoloStats — keep it, DB validator
        # will match by jersey number anyway
        if "player_name" not in data:
            data["player_name"] = f"#{pn}"

        # Default missing numeric fields to 0
        for csv_col, model_field in CSV_TO_MODEL.items():
            if model_field not in ("player_name", "position", "jersey_number"):
                data.setdefault(model_field, 0)

        data.setdefault("position", "")
        rows.append(data)

    return {"rows": rows, "errors": errors, "warnings": warnings}


def validate_against_db(
    parsed_rows: list[dict],
    match_id: int,
    team_id: int | None = None,
) -> dict[str, Any]:
    """
    Cross-check parsed rows against database state.

    Parameters
    ----------
    parsed_rows : list[dict]
        Output of ``parse_csv``'s ``rows`` key.
    match_id : int
        PK of the match these stats belong to.
    team_id : int | None
        When supplied, only match players against that team's roster.

    Returns
    -------
    dict with keys ``valid_rows``, ``unmatched_players``, ``errors``.
    """
    from .models import Match, Player

    errors: list[str] = []
    valid_rows: list[dict] = []
    unmatched: list[dict] = []

    try:
        match = Match.objects.select_related("team_a", "team_b").get(pk=match_id)
    except Match.DoesNotExist:
        return {
            "valid_rows": [],
            "unmatched_players": [],
            "errors": [f"Match with id={match_id} does not exist."],
        }

    # Determine which teams' rosters to load
    teams = list(filter(None, [match.team_a, match.team_b]))
    if team_id:
        teams = [t for t in teams if t.pk == team_id]
        if not teams:
            return {
                "valid_rows": [],
                "unmatched_players": [],
                "errors": ["Selected team is not part of this match."],
            }

    team_names = {t.name.lower() for t in teams}

    # Build jersey → Player index
    roster: dict[tuple[str, str], Player] = {}
    for team in teams:
        for p in team.players.all():
            if p.jersey_number is not None:
                roster[(team.name.lower(), p.jersey_number)] = p

    for row in parsed_rows:
        team_key = row.get("_team_name", "").lower()
        jersey = row.get("jersey_number")

        if team_key and team_key not in team_names:
            errors.append(
                f"Row player '{row.get('player_name')}': team '{row.get('_team_name')}' "
                f"does not match either team in match M{match.match_number}."
            )
            continue

        # Resolve player from roster
        player = roster.get((team_key, jersey)) if team_key and jersey else None

        if player is None:
            # Try matching by jersey only across both teams
            for tn in team_names:
                player = roster.get((tn, jersey))
                if player:
                    team_key = tn
                    break

        if player is None:
            unmatched.append(row)
        else:
            row["_player_id"] = player.pk
            row["_team_id"] = player.team_id
            valid_rows.append(row)

    return {
        "valid_rows": valid_rows,
        "unmatched_players": unmatched,
        "errors": errors,
    }


# ── Private ──────────────────────────────────────────────


def _split_sections(raw: str) -> list[str]:
    """Split a multi-section CSV into individual CSV texts.

    Sections are separated by one or more blank lines.  Each section
    starts with a header row.
    """
    sections: list[str] = []
    current_lines: list[str] = []

    for line in raw.splitlines():
        stripped = line.strip().rstrip(",")
        if not stripped:
            if current_lines:
                sections.append("\n".join(current_lines))
                current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append("\n".join(current_lines))

    return sections


def _extract_fields(
    raw_row: dict,
    header_map: dict[str, str],
    target: dict[str, Any],
    sec_idx: int,
    line_no: int,
) -> tuple[list[str], list[str]]:
    """Extract known model fields from a single CSV row into *target* dict."""
    errors: list[str] = []
    warnings: list[str] = []

    for csv_col, model_field in CSV_TO_MODEL.items():
        if model_field == "jersey_number":
            continue  # handled by caller via Player Number key

        original_header = header_map.get(csv_col)
        if original_header is None:
            continue  # column not in this section

        value = (raw_row.get(original_header) or "").strip()

        if model_field == "player_name":
            if value:
                target["player_name"] = value
            continue

        if model_field == "position":
            if value:
                upper = value.upper()
                if upper in _VALID_POSITIONS:
                    target["position"] = upper
                else:
                    warnings.append(
                        f"Section {sec_idx}, row {line_no}: "
                        f"position '{value}' not recognised, storing as-is."
                    )
                    target["position"] = value
            continue

        # Numeric field
        if not value or value == "-":
            # Don't overwrite a value already set by an earlier section
            target.setdefault(model_field, 0)
            continue
        try:
            int_val = int(value)
        except ValueError:
            errors.append(
                f"Section {sec_idx}, row {line_no}: "
                f"'{csv_col}' has non-integer value '{value}'."
            )
            continue
        if int_val < 0:
            errors.append(
                f"Section {sec_idx}, row {line_no}: "
                f"'{csv_col}' is negative ({int_val})."
            )
            continue
        target[model_field] = int_val

    # Carry raw team name if present
    team_header = header_map.get("Team Name") or header_map.get("Team")
    if team_header:
        team_val = (raw_row.get(team_header) or "").strip()
        if team_val:
            target["_team_name"] = team_val

    return errors, warnings

    return out, errors, warnings
