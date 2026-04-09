"""
XML parser and database validator for SoloStats Live WebReports exports.

Parses ``<vbgame>`` XML files and returns the same dict format as
``csv_import.parse_csv`` for seamless integration with the import pipeline.
"""

from __future__ import annotations

import defusedxml.ElementTree as ET
from typing import Any

from .constants import POSITION_CHOICES
from .csv_mapping import SKIP_PLAYER_NUMBERS
from .xml_mapping import (
    BLOCK_ATTRS,
    PLAYER_JERSEY_ATTR,
    PLAYER_NAME_ATTR,
    PLAYER_POSITION_ATTR,
    PLAYER_SETS_PLAYED_ATTR,
    XML_TO_MODEL,
)

_VALID_POSITIONS = {code for code, _ in POSITION_CHOICES}


# ── Public API ───────────────────────────────────────────


def parse_xml(file_obj) -> dict[str, Any]:
    """
    Parse a SoloStats Live XML (WebReports) file into player-stat dicts.

    Returns dict with keys ``rows``, ``errors``, ``warnings`` — same
    structure as ``csv_import.parse_csv``.
    """
    try:
        if hasattr(file_obj, "read"):
            raw = file_obj.read()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8-sig")
        else:
            raw = str(file_obj)
    except Exception as exc:
        return {"rows": [], "errors": [f"Cannot read XML: {exc}"], "warnings": []}

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        return {"rows": [], "errors": [f"Invalid XML: {exc}"], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []

    # Find all <team> elements (may be under <vbgame> or nested deeper)
    teams = root.findall(".//team")
    if not teams:
        return {"rows": [], "errors": ["No <team> elements found in XML."], "warnings": []}

    for team_el in teams:
        team_name = team_el.get("name", "").strip()

        for player_el in team_el.findall("player"):
            row = _parse_player(player_el, team_name, errors, warnings)
            if row is not None:
                rows.append(row)

    if not rows and not errors:
        errors.append("No player data found in XML.")

    return {"rows": rows, "errors": errors, "warnings": warnings}


def _parse_player(
    player_el,
    team_name: str,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any] | None:
    """Extract stats from a single ``<player>`` element."""
    jersey = (player_el.get(PLAYER_JERSEY_ATTR) or "").strip()
    if not jersey or jersey.lower() in SKIP_PLAYER_NUMBERS:
        return None

    name = (player_el.get(PLAYER_NAME_ATTR) or "").strip() or f"#{jersey}"
    position = (player_el.get(PLAYER_POSITION_ATTR) or "").strip().upper()

    if position and position not in _VALID_POSITIONS:
        warnings.append(f"Player '{name}' (#{jersey}): position '{position}' not recognised.")
        position = ""

    row: dict[str, Any] = {
        "player_name": name,
        "jersey_number": jersey,
        "position": position,
        "_team_name": team_name,
    }

    # sets played (gp attribute on <player>)
    gp = player_el.get(PLAYER_SETS_PLAYED_ATTR, "0")
    row["sets_played"] = _safe_int(gp, 0)

    # Stat sub-elements
    for (tag, attr), model_field in XML_TO_MODEL.items():
        el = player_el.find(tag)
        if el is None:
            row.setdefault(model_field, 0)
            continue
        val = _safe_int(el.get(attr, "0"), 0)
        # For defense/dig aliases: take the first non-zero value
        if model_field in row and row[model_field] != 0:
            continue
        row[model_field] = val

    # Blocks: bs (solo) + ba (assist) = total
    block_el = player_el.find("block")
    if block_el is not None:
        total_blocks = sum(
            _safe_int(block_el.get(a, "0"), 0) for a in BLOCK_ATTRS
        )
        row["blocks"] = total_blocks
    else:
        row.setdefault("blocks", 0)

    # Ensure all numeric fields have defaults
    for field in (
        "serve_attempts", "aces", "serve_errors",
        "kills", "attack_errors",
        "pass_errors",
        "blocks", "assists", "setting_errors", "sets_played",
    ):
        row.setdefault(field, 0)

    return row


def _safe_int(value: str, default: int = 0) -> int:
    """Convert string to non-negative int, returning *default* on failure."""
    try:
        v = int(value)
        return v if v >= 0 else default
    except (ValueError, TypeError):
        return default
