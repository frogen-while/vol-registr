"""
Business-logic layer for tournament registration.

Keeps views thin by encapsulating creation / parsing
logic in pure-Python functions that are easy to test.
"""

from __future__ import annotations

from django.db import transaction

from .constants import MAX_TOURNAMENT_SLOTS, PAYMENT_ACCEPTED, PAYMENT_WAITING
from .models import Player, Team


# ── Public API ───────────────────────────────────────────

def get_available_slots() -> int:
    """Return remaining open slots based on accepted teams."""
    approved = Team.objects.filter(payment_status=PAYMENT_ACCEPTED).count()
    return max(MAX_TOURNAMENT_SLOTS - approved, 0)


@transaction.atomic
def register_team(cleaned: dict) -> Team:
    """
    Create a Team (+ optional Players) from validated form data.

    Parameters
    ----------
    cleaned : dict
        Output of ``TeamRegistrationForm.cleaned_data``.

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

    team = Team.objects.create(
        name=team_name,
        division=cleaned["division"],
        city=cleaned.get("city", ""),
        cap_name=cap["first"],
        cap_surname=cap["last"],
        cap_phone=cleaned.get("phone", ""),
        cap_email=email,
        payment_status=PAYMENT_WAITING,
    )

    roster_text = cleaned.get("roster", "")
    if roster_text:
        _create_players_from_roster(team, roster_text)

    return team


# ── Private Helpers ──────────────────────────────────────

def _create_players_from_roster(team: Team, roster_text: str) -> None:
    """
    Parse a comma-separated roster string and bulk-create Player rows.

    Expected format: ``"John Doe 10, Jane Smith 12"``
    The trailing number (jersey) is optional.
    """
    raw_entries = [entry.strip() for entry in roster_text.split(",") if entry.strip()]
    players_to_create: list[Player] = []

    for entry in raw_entries:
        first_name, last_name, jersey_number = _parse_player_entry(entry)
        if first_name:
            players_to_create.append(
                Player(
                    team=team,
                    first_name=first_name,
                    last_name=last_name,
                    jersey_number=jersey_number,
                )
            )

    if players_to_create:
        Player.objects.bulk_create(players_to_create)


def _parse_player_entry(entry: str) -> tuple[str, str, int | None]:
    """
    Extract (first_name, last_name, jersey_number) from a single roster entry.

    Returns
    -------
    tuple[str, str, int | None]
        A 3-tuple; jersey_number is ``None`` when not present.
    """
    parts = entry.split()
    if not parts:
        return ("", "", None)

    jersey_number = None
    if parts[-1].isdigit():
        jersey_number = int(parts[-1])
        name_parts = parts[:-1]
    else:
        name_parts = parts

    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    return (first_name, last_name, jersey_number)
