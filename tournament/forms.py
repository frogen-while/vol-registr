"""
Django forms for tournament team registration.

Handles input validation and sanitization
before data reaches the service layer.
"""

from django import forms

from .constants import DIVISION_CHOICES


class TeamRegistrationForm(forms.Form):
    """Validates the JSON payload sent from the registration page."""

    teamName = forms.CharField(max_length=100, strip=True)
    division = forms.ChoiceField(choices=DIVISION_CHOICES)
    city = forms.CharField(max_length=100, required=False, strip=True)

    capName = forms.CharField(max_length=100, strip=True)
    phone = forms.CharField(max_length=20, required=False, strip=True)
    email = forms.EmailField(max_length=100)

    roster = forms.CharField(required=False, strip=True)

    def clean_capName(self):
        """Split full name into (first, last) tuple stored in cleaned_data."""
        full_name = self.cleaned_data["capName"]
        parts = full_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
        # Store both pieces; the original key is replaced with a dict
        return {"first": first_name, "last": last_name}
