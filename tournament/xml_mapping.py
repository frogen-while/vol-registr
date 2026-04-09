"""
Attribute mappings from SoloStats Live XML (WebReports) to Django model fields.

SoloStats exports a ``<vbgame>`` XML with ``<team>`` / ``<player>`` nodes.
Each ``<player>`` contains sub-elements like ``<attack>``, ``<serve>``, etc.
whose *attributes* hold the numeric stat values.
"""

# ── XML element/attribute → model field ──────────────────
# Key format: ("sub-element-tag", "attribute")
# Value: model field name on PlayerMatchStats
XML_TO_MODEL: dict[tuple[str, str], str] = {
    ("attack", "k"): "kills",
    ("attack", "e"): "attack_errors",
    ("set", "a"): "assists",
    ("set", "e"): "setting_errors",
    ("serve", "sa"): "aces",
    ("serve", "se"): "serve_errors",
    ("serve", "ta"): "serve_attempts",
    ("defense", "re"): "pass_errors",
    ("dig", "re"): "pass_errors",          # alias: some exports use <dig>
}

# Block is special: solo blocks (bs) + assist blocks (ba) = total blocks
BLOCK_ATTRS = ("bs", "ba")

# Player-level attributes
PLAYER_JERSEY_ATTR = "uni"          # uniform / jersey number
PLAYER_SETS_PLAYED_ATTR = "gp"     # games (sets) played
PLAYER_NAME_ATTR = "name"
PLAYER_POSITION_ATTR = "pos"


