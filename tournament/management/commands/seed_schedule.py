"""
Seed the 28-match tournament schedule.

Usage:
    python manage.py seed_schedule --date 2026-07-11
"""

from __future__ import annotations

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tournament.constants import (
    MATCH_FINISHED,
    MATCH_SCHEDULED,
    STAGE_FINAL,
    STAGE_GROUP,
    STAGE_PLACE_3,
    STAGE_PLACE_5,
    STAGE_PLACE_7,
    STAGE_PLACE_9,
    STAGE_PLACE_11,
    STAGE_QF,
    STAGE_SF_1_4,
    STAGE_SF_5_8,
    STAGE_SF_9_12,
)
from tournament.models import Match, Team


# (match_number, time_offset_minutes, court, stage, group, home_name, away_name, score_a, score_b, status)
SCHEDULE = [
    # ── Groups Round 1: 09:00 ──
    (1,   0, 1, STAGE_GROUP, "A", "Pocket Aces Black", "Court Kings",     2, 0, MATCH_FINISHED),
    (2,   0, 2, STAGE_GROUP, "B", "Lodz Spikers",     "Baseline Crew",   2, 0, MATCH_FINISHED),
    (3,   0, 3, STAGE_GROUP, "C", "North Side Six",   "Volley Forge",    2, 1, MATCH_FINISHED),
    # ── Groups Round 2: 10:10 ──
    (4,  70, 1, STAGE_GROUP, "D", "Quick Six",        "Block Unit",      2, 0, MATCH_FINISHED),
    (5,  70, 2, STAGE_GROUP, "A", "Skyblock",         "Court Kings",     2, 1, MATCH_FINISHED),
    (6,  70, 3, STAGE_GROUP, "B", "Warsaw Eagles",    "Baseline Crew",   2, 0, MATCH_FINISHED),
    # ── Groups Round 3: 11:20 ──
    (7, 140, 1, STAGE_GROUP, "C", "Red Tempo",        "Volley Forge",    2, 0, MATCH_FINISHED),
    (8, 140, 2, STAGE_GROUP, "D", "Metro Spin",       "Block Unit",      2, 0, MATCH_FINISHED),
    (9, 140, 3, STAGE_GROUP, "A", "Pocket Aces Black", "Skyblock",       2, 1, MATCH_FINISHED),
    # ── Groups Round 4: 12:30 ──
    (10, 210, 1, STAGE_GROUP, "B", "Lodz Spikers",    "Warsaw Eagles",   2, 0, MATCH_FINISHED),
    (11, 210, 2, STAGE_GROUP, "C", "North Side Six",  "Red Tempo",       2, 1, MATCH_FINISHED),
    (12, 210, 3, STAGE_GROUP, "D", "Quick Six",       "Metro Spin",      2, 1, MATCH_FINISHED),
    # ── Quarter-Finals: 14:00, 14:50 ──
    (13, 300, 1, STAGE_QF, "", "Pocket Aces Black", "Warsaw Eagles", 2, 0, MATCH_FINISHED),
    (14, 300, 2, STAGE_QF, "", "North Side Six",    "Metro Spin",    2, 1, MATCH_FINISHED),
    (15, 300, 3, STAGE_QF, "", "Lodz Spikers",      "Skyblock",      2, 0, MATCH_FINISHED),
    (16, 350, 1, STAGE_QF, "", "Quick Six",          "Red Tempo",     2, 1, MATCH_FINISHED),
    # ── Semi-Finals: 15:30, 16:20 ──
    (17, 390, 1, STAGE_SF_1_4, "", "Pocket Aces Black", "North Side Six", 2, 1, MATCH_FINISHED),
    (18, 390, 2, STAGE_SF_1_4, "", "Lodz Spikers",      "Quick Six",      2, 0, MATCH_FINISHED),
    (19, 390, 3, STAGE_SF_5_8, "", "Warsaw Eagles",     "Metro Spin",     2, 0, MATCH_FINISHED),
    (20, 440, 1, STAGE_SF_5_8, "", "Skyblock",          "Red Tempo",      2, 1, MATCH_FINISHED),
    (21, 440, 2, STAGE_SF_9_12, "", "Court Kings",      "Baseline Crew",  0, 2, MATCH_FINISHED),
    (22, 440, 3, STAGE_SF_9_12, "", "Volley Forge",     "Block Unit",     2, 1, MATCH_FINISHED),
    # ── Placement: 18:00 ──
    (23, 540, 1, STAGE_PLACE_7,  "", "Metro Spin",     "Red Tempo",      0, 0, MATCH_SCHEDULED),
    (24, 540, 2, STAGE_PLACE_9,  "", "Baseline Crew",  "Volley Forge",   0, 0, MATCH_SCHEDULED),
    (25, 540, 3, STAGE_PLACE_11, "", "Court Kings",     "Block Unit",     0, 0, MATCH_SCHEDULED),
    # ── 3rd / 5th: 18:50 ──
    (26, 590, 2, STAGE_PLACE_3, "", "North Side Six",  "Quick Six",       0, 0, MATCH_SCHEDULED),
    (27, 590, 3, STAGE_PLACE_5, "", "Warsaw Eagles",   "Skyblock",        0, 0, MATCH_SCHEDULED),
    # ── Final: 19:40 ──
    (28, 640, 1, STAGE_FINAL, "", "Pocket Aces Black", "Lodz Spikers",   0, 0, MATCH_SCHEDULED),
]


def _next_saturday():
    today = timezone.now().date()
    days_ahead = 5 - today.weekday()  # Saturday = 5
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


class Command(BaseCommand):
    help = "Create the 28-match tournament schedule."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Tournament date as YYYY-MM-DD (default: next Saturday)",
        )

    def handle(self, *args, **options):
        date_str = options["date"]
        if date_str:
            base_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            base_date = _next_saturday()

        base_dt = timezone.make_aware(
            datetime.combine(base_date, datetime.min.time().replace(hour=9))
        )

        created = 0
        skipped = 0

        for row in SCHEDULE:
            (
                match_number, offset_min, court, stage, group,
                home_name, away_name, score_a, score_b, status,
            ) = row

            if Match.objects.filter(match_number=match_number).exists():
                skipped += 1
                continue

            team_a = self._get_team(home_name)
            team_b = self._get_team(away_name)

            Match.objects.create(
                match_number=match_number,
                stage=stage,
                group=group,
                court=court,
                start_time=base_dt + timedelta(minutes=offset_min),
                team_a=team_a,
                team_b=team_b,
                score_a=score_a,
                score_b=score_b,
                status=status,
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Schedule seeded: {created} created, {skipped} skipped (date={base_date})"
            )
        )

    def _get_team(self, name: str):
        try:
            return Team.objects.get(name=name)
        except Team.DoesNotExist:
            self.stderr.write(self.style.WARNING(f"  Team '{name}' not found — leaving NULL"))
            return None
