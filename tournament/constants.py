"""
Tournament-wide constants and configuration values.

Centralizes all magic numbers, choices, and config
so they can be changed in one place.
"""

# ── Slot / Capacity ─────────────────────────────────────
MAX_TOURNAMENT_SLOTS = 12

# ── League Level Choices ────────────────────────────────────
LEAGUE_LEVEL_1ST = "1st"
LEAGUE_LEVEL_2ND = "2nd"
LEAGUE_LEVEL_3RD = "3rd"
LEAGUE_LEVEL_INDEPENDENT = "independent"

LEAGUE_LEVEL_CHOICES = [
    (LEAGUE_LEVEL_1ST, "1st Liga"),
    (LEAGUE_LEVEL_2ND, "2nd Liga"),
    (LEAGUE_LEVEL_3RD, "3rd Liga"),
    (LEAGUE_LEVEL_INDEPENDENT, "Independent Team"),
]

# ── Payment Status ───────────────────────────────────────
PAYMENT_WAITING = 0
PAYMENT_ACCEPTED = 1
PAYMENT_REFUND = 2

PAYMENT_STATUS_CHOICES = [
    (PAYMENT_WAITING, "Waiting"),
    (PAYMENT_ACCEPTED, "Accepted"),
    (PAYMENT_REFUND, "Refund"),
]

# ── Field Limits ─────────────────────────────────────────
TEAM_NAME_MAX_LENGTH = 100
CITY_MAX_LENGTH = 100
PERSON_NAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 100
PHONE_MAX_LENGTH = 20
LOGO_PATH_MAX_LENGTH = 255
GROUP_NAME_MAX_LENGTH = 10

# ── DB Table Names ───────────────────────────────────────
TABLE_TEAMS = "Teams"
TABLE_PLAYERS = "Players"
