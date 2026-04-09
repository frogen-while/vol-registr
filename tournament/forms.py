"""
Django forms for tournament team registration.

Handles input validation and sanitization
before data reaches the service layer.
"""

from django import forms

from .constants import LEAGUE_LEVEL_CHOICES


class PlayerForm(forms.Form):
    """Validates a single player entry in the roster."""

    firstName    = forms.CharField(max_length=50, strip=True)
    lastName     = forms.CharField(max_length=50, strip=True)
    jerseyNumber = forms.IntegerField(required=False, min_value=0, max_value=99)


class TeamRegistrationForm(forms.Form):
    """Validates the JSON payload sent from the 3-step registration page."""

    # ── Step 1: Team Identity ───────────────────────────────
    teamName    = forms.CharField(max_length=100, strip=True)
    leagueLevel = forms.ChoiceField(choices=LEAGUE_LEVEL_CHOICES)

    # ── Step 2: Captain ─────────────────────────────────────
    capName   = forms.CharField(max_length=100, strip=True)
    phone     = forms.CharField(max_length=20, required=False, strip=True)
    email     = forms.EmailField(max_length=100)

    def clean_capName(self):
        """Split full name into (first, last) dict stored in cleaned_data."""
        full_name = self.cleaned_data["capName"]
        parts = full_name.split(" ", 1)
        return {
            "first": parts[0],
            "last": parts[1] if len(parts) > 1 else "",
        }
