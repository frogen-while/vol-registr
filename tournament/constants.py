"""
Tournament-wide constants and configuration values.

Centralizes all magic numbers, choices, and config
so they can be changed in one place.
"""

# ── Slot / Capacity ─────────────────────────────────────
MAX_TOURNAMENT_SLOTS = 10

# ── Registration Gate ───────────────────────────────────
REGISTRATION_CLOSED = False
REGISTRATION_DEADLINE_ISO = "2026-05-21T00:00:00+02:00"

# ── Payment Status ───────────────────────────────────────
PAYMENT_WAITING = 0
PAYMENT_ACCEPTED = 1
PAYMENT_REFUND = 2

PAYMENT_STATUS_CHOICES = [
    (PAYMENT_WAITING, "Waiting"),
    (PAYMENT_ACCEPTED, "Accepted"),
    (PAYMENT_REFUND, "Refund"),
]

# ── Team Status (registration workflow) ──────────────────
TEAM_STATUS_REGISTERED = "REGISTERED"
TEAM_STATUS_AWAITING_PAYMENT = "AWAITING_PAYMENT"
TEAM_STATUS_PAID = "PAID"
TEAM_STATUS_APPROVED = "APPROVED"

TEAM_STATUS_CHOICES = [
    (TEAM_STATUS_REGISTERED, "Registered"),
    (TEAM_STATUS_AWAITING_PAYMENT, "Awaiting Payment"),
    (TEAM_STATUS_PAID, "Paid"),
    (TEAM_STATUS_APPROVED, "Approved"),
]

# ── Payment Accounts ──────────────────────────────────
PAYMENT_ACCOUNTS = [
    {"blik": "793 424 526", "capacity": 6},
    {"blik": "572 637 803", "capacity": 3},
    {"blik": "535 054 366", "capacity": 3},
]

# ── Field Limits ─────────────────────────────────────────
TEAM_NAME_MAX_LENGTH = 100
PERSON_NAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 100
PHONE_MAX_LENGTH = 20

# ── Feature Toggles ─────────────────────────────────────
FAN_VOTING_ENABLED = True
LOGO_PATH_MAX_LENGTH = 255
GROUP_NAME_MAX_LENGTH = 10

# ── Match Status ──────────────────────────────────────────
MATCH_SCHEDULED = "SCHEDULED"
MATCH_LIVE = "LIVE"
MATCH_FINISHED = "FINISHED"
MATCH_POSTPONED = "POSTPONED"

MATCH_STATUS_CHOICES = [
    (MATCH_SCHEDULED, "Scheduled"),
    (MATCH_LIVE, "Live"),
    (MATCH_FINISHED, "Finished"),
    (MATCH_POSTPONED, "Postponed"),
]

# ── Stage Choices ─────────────────────────────────────────
STAGE_GROUP = "GROUP"
STAGE_QF = "QF"
STAGE_SF_1_4 = "SF_1_4"
STAGE_SF_5_8 = "SF_5_8"
STAGE_SF_9_12 = "SF_9_12"
STAGE_PLACE_11 = "PLACE_11"
STAGE_PLACE_9 = "PLACE_9"
STAGE_PLACE_7 = "PLACE_7"
STAGE_PLACE_5 = "PLACE_5"
STAGE_PLACE_3 = "PLACE_3"
STAGE_FINAL = "FINAL"

STAGE_CHOICES = [
    (STAGE_GROUP, "Group Stage"),
    (STAGE_QF, "Quarter-Final"),
    (STAGE_SF_1_4, "Semi-Final 1–4"),
    (STAGE_SF_5_8, "Semi-Final 5–8"),
    (STAGE_SF_9_12, "Semi-Final 9–12"),
    (STAGE_PLACE_11, "11th Place"),
    (STAGE_PLACE_9, "9th Place"),
    (STAGE_PLACE_7, "7th Place"),
    (STAGE_PLACE_5, "5th Place"),
    (STAGE_PLACE_3, "3rd Place"),
    (STAGE_FINAL, "Final"),
]

# ── Court Choices ─────────────────────────────────────────
COURT_CHOICES = [
    (1, "Court 1"),
    (2, "Court 2"),
    (3, "Court 3"),
]

# ── Schedule Event Types ──────────────────────────────────
EVENT_OPENING = "OPENING"
EVENT_BREAK = "BREAK"
EVENT_CEREMONY = "CEREMONY"
EVENT_OTHER = "OTHER"

EVENT_TYPE_CHOICES = [
    (EVENT_OPENING, "Opening Ceremony"),
    (EVENT_BREAK, "Break"),
    (EVENT_CEREMONY, "Award Ceremony"),
    (EVENT_OTHER, "Other"),
]

# ── Player Position ───────────────────────────────────────
POSITION_OH = "OH"
POSITION_MB = "MB"
POSITION_S = "S"
POSITION_OPP = "OPP"
POSITION_L = "L"

POSITION_CHOICES = [
    (POSITION_OH, "Outside Hitter"),
    (POSITION_MB, "Middle Blocker"),
    (POSITION_S, "Setter"),
    (POSITION_OPP, "Opposite"),
    (POSITION_L, "Libero"),
]

# ── MVP Type ──────────────────────────────────────────────
MVP_MATCH = "MATCH_MVP"
MVP_TOURNAMENT = "TOURNAMENT_MVP"

MVP_TYPE_CHOICES = [
    (MVP_MATCH, "Match MVP"),
    (MVP_TOURNAMENT, "Tournament MVP"),
]

# ── MVP Weighted Scoring (per-set) ────────────────────────
# Each position uses: sum(field * weight for field, weight) / sets_played
# Positive = good stats, negative = errors to penalise
# OH: Outside Hitter
# OPP: Opposite
# MB: Middle Blocker
# S: Setter
# L: Libero — uses -pass_errors / sets (closest to 0 wins)
MVP_WEIGHTS = {
    POSITION_OH: [
        ("kills", 1.0),
        ("aces", 1.5),
        ("blocks", 1.5),
        ("attack_errors", -1.0),
        ("serve_errors", -0.8),
        ("pass_errors", -0.5),
    ],
    POSITION_OPP: [
        ("kills", 1.0),
        ("aces", 1.5),
        ("blocks", 1.5),
        ("attack_errors", -1.0),
        ("serve_errors", -0.8),
    ],
    POSITION_MB: [
        ("kills", 1.0),
        ("blocks", 2.0),
        ("aces", 1.5),
        ("attack_errors", -1.0),
        ("serve_errors", -0.8),
    ],
    POSITION_S: [
        ("assists", 1.0),
        ("aces", 2.0),
        ("kills", 2.0),
        ("setting_errors", -1.5),
        ("serve_errors", -1.0),
        ("attack_errors", -1.0),
    ],
    POSITION_L: [
        ("pass_errors", -1.0),
    ],
}

# ── Roster Access ─────────────────────────────────────
ROSTER_CODE_LENGTH = 6

# ── DB Table Names ───────────────────────────────────────
TABLE_TEAMS = "Teams"
TABLE_PLAYERS = "Players"
TABLE_MATCHES = "matches"
TABLE_GAME_SETS = "game_sets"
TABLE_PLAYER_MATCH_STATS = "player_match_stats"
TABLE_TEAM_MATCH_STATS = "team_match_stats"
TABLE_GROUP_STANDINGS = "group_standings"
TABLE_DREAM_TEAM = "dream_team"
TABLE_MVP_SELECTIONS = "mvp_selections"
TABLE_MATCH_HIGHLIGHTS = "match_highlights"
TABLE_GALLERY_PHOTOS = "gallery_photos"
TABLE_GALLERY_VIDEOS = "gallery_videos"
TABLE_AUDIT_ENTRIES = "audit_entries"
TABLE_SCHEDULE_EVENTS = "schedule_events"
