"""
Seed group assignments and initial GroupStanding rows.

Usage:
    python manage.py seed_groups
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from tournament.models import GroupStanding, Team

# team name → group
GROUP_ASSIGNMENTS = {
    "Pocket Aces Black": "A",
    "Skyblock": "A",
    "Court Kings": "A",
    "Lodz Spikers": "B",
    "Warsaw Eagles": "B",
    "Baseline Crew": "B",
    "North Side Six": "C",
    "Red Tempo": "C",
    "Volley Forge": "C",
    "Quick Six": "D",
    "Metro Spin": "D",
    "Block Unit": "D",
}


class Command(BaseCommand):
    help = "Assign 12 teams to 4 groups (A-D) and create GroupStanding rows."

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        missing = 0

        for team_name, group in GROUP_ASSIGNMENTS.items():
            try:
                team = Team.objects.get(name=team_name)
            except Team.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"  Team '{team_name}' not found — skipping"))
                missing += 1
                continue

            # Update Team.group_name
            if team.group_name != group:
                team.group_name = group
                team.save(update_fields=["group_name"])

            # Create or skip GroupStanding
            _, was_created = GroupStanding.objects.get_or_create(
                team=team,
                defaults={"group": group},
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Groups seeded: {created} created, {skipped} existing, {missing} teams not found"
            )
        )
