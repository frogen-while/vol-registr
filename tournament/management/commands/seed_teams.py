"""
Seed the 12 demo tournament teams.

Run this BEFORE seed_schedule, seed_groups, and seed_demo_stats.

Usage:
    python manage.py seed_teams
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from tournament.models import Team

# (name, cap_name, cap_surname, cap_email)
DEMO_TEAMS = [
    ("Pocket Aces Black", "Daria", "Yasenovska", "demo-pa@example.com"),
    ("Skyblock",          "Alex",  "Nowak",      "demo-sky@example.com"),
    ("Court Kings",       "Jan",   "Kowalski",   "demo-ck@example.com"),
    ("Lodz Spikers",      "Maja",  "Wozniak",    "demo-ls@example.com"),
    ("Warsaw Eagles",     "Tomek", "Lewandowski","demo-we@example.com"),
    ("Baseline Crew",     "Anna",  "Sikora",     "demo-bc@example.com"),
    ("North Side Six",    "Kasia", "Grudzien",   "demo-ns@example.com"),
    ("Red Tempo",         "Piotr", "Zieliński",  "demo-rt@example.com"),
    ("Volley Forge",      "Ola",   "Duda",       "demo-vf@example.com"),
    ("Quick Six",         "Marek", "Wiśniewski", "demo-qs@example.com"),
    ("Metro Spin",        "Nina",  "Polak",      "demo-ms@example.com"),
    ("Block Unit",        "Igor",  "Kamiński",   "demo-bu@example.com"),
]


class Command(BaseCommand):
    help = "Create 12 demo tournament teams (skips existing ones)."

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for name, cap_name, cap_surname, cap_email in DEMO_TEAMS:
            if Team.objects.filter(name=name).exists():
                skipped += 1
                continue

            Team.objects.create(
                name=name,
                cap_name=cap_name,
                cap_surname=cap_surname,
                cap_email=cap_email,
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Demo teams: {created} created, {skipped} existing")
        )
