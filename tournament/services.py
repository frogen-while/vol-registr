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
def register_team(cleaned: dict, players_data: list[dict] | None = None) -> Team:
    """
    Create a Team (+ Players) from validated form data.

    Parameters
    ----------
    cleaned : dict
        Output of ``TeamRegistrationForm.cleaned_data``.
    players_data : list[dict] | None
        List of player dicts from the request (validated outside the form).

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

    phone = cleaned.get("phone") or None
    if phone and Team.objects.filter(cap_phone=phone).exists():
        raise ValueError("This phone number is already registered.")

    team = Team.objects.create(
        name=team_name,
        league_level=cleaned["leagueLevel"],
        city=cleaned.get("city", ""),
        instagram=cleaned.get("instagram", ""),
        cap_name=cap["first"],
        cap_surname=cap["last"],
        cap_dob=cleaned.get("capDob"),
        cap_jersey=cleaned.get("capJersey"),
        cap_phone=phone,
        cap_email=email,
        payment_status=PAYMENT_WAITING,
    )

    if players_data:
        _create_players(team, players_data)

    return team


# ── Private Helpers ──────────────────────────────────────

def _create_players(team: Team, players_data: list[dict]) -> None:
    """
    Bulk-create Player rows from a list of validated player dicts.

    Each dict is expected to have keys: firstName, lastName,
    jerseyNumber (optional), dob (optional date string / date).
    """
    from .forms import PlayerForm

    players_to_create: list[Player] = []
    for entry in players_data:
        form = PlayerForm(entry)
        if not form.is_valid():
            continue  # skip malformed entries rather than hard-fail

        cd = form.cleaned_data
        first = cd.get("firstName", "").strip()
        if not first:
            continue

        players_to_create.append(
            Player(
                team=team,
                first_name=first,
                last_name=cd.get("lastName", "").strip(),
                jersey_number=cd.get("jerseyNumber"),
                date_of_birth=cd.get("dob"),
            )
        )

    if players_to_create:
        Player.objects.bulk_create(players_to_create)

