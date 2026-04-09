"""
Column mappings from SoloStats Live CSV exports to Django model fields.

SoloStats exports a single CSV with multiple sections (each has its own
header row).  The parser merges sections by player key (Player Number).
"""

# ── CSV header → model field (canonical names) ──────────
CSV_TO_MODEL = {
    "Player Name": "player_name",
    "Player Number": "jersey_number",
    "Position": "position",
    "Serve Attempts": "serve_attempts",
    "Aces": "aces",
    "Serve Errors": "serve_errors",
    "Attack Attempts": "attack_attempts",
    "Kills": "kills",
    "Attack Errors": "attack_errors",
    "Pass Attempts": "pass_attempts",
    "3-pass": "perfect_passes",
    "Total Pass Errors": "pass_errors",
    "Blocks": "blocks",
    "Assists": "assists",
    "Setting Errors": "setting_errors",
}

# Alternative header names that map to the same canonical name.
COLUMN_ALIASES = {
    "Jersey": "Player Number",
    "Perfect Passes": "3-pass",
    "Pass Errors": "Total Pass Errors",
}

# Columns that must appear across ALL sections combined.
REQUIRED_COLUMNS = {"Player Name", "Player Number", "Kills", "Aces", "Blocks"}

# Columns whose values are numeric integers.
NUMERIC_COLUMNS = {
    k for k, v in CSV_TO_MODEL.items()
    if v not in ("player_name", "position")
}

# Rows to skip (aggregation rows from SoloStats).
SKIP_PLAYER_NUMBERS = {"total", "undefined"}
