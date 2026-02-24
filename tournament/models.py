from django.db import models

from .constants import (
    CITY_MAX_LENGTH,
    DIVISION_CHOICES,
    DIVISION_PRO_MEN,
    EMAIL_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    LOGO_PATH_MAX_LENGTH,
    PAYMENT_STATUS_CHOICES,
    PAYMENT_WAITING,
    PERSON_NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    TABLE_PLAYERS,
    TABLE_TEAMS,
    TEAM_NAME_MAX_LENGTH,
)


class Team(models.Model):
    """A registered tournament team with captain contact details."""

    name = models.CharField(
        max_length=TEAM_NAME_MAX_LENGTH, unique=True, verbose_name="Team Name"
    )
    logo_path = models.CharField(
        max_length=LOGO_PATH_MAX_LENGTH, blank=True, null=True
    )
    city = models.CharField(
        max_length=CITY_MAX_LENGTH, blank=True, null=True, verbose_name="City / Club"
    )
    division = models.CharField(
        max_length=50, choices=DIVISION_CHOICES, default=DIVISION_PRO_MEN
    )
    group_name = models.CharField(
        max_length=GROUP_NAME_MAX_LENGTH, blank=True, null=True
    )

    # Captain information
    cap_name = models.CharField(
        max_length=PERSON_NAME_MAX_LENGTH, verbose_name="Captain Name"
    )
    cap_surname = models.CharField(
        max_length=PERSON_NAME_MAX_LENGTH, verbose_name="Captain Surname"
    )
    cap_email = models.EmailField(max_length=EMAIL_MAX_LENGTH, unique=True)
    cap_phone = models.CharField(
        max_length=PHONE_MAX_LENGTH, unique=True, blank=True, null=True
    )

    payment_status = models.IntegerField(
        choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_WAITING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = TABLE_TEAMS
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_payment_status_display()})"


class Player(models.Model):
    """An individual player belonging to a team roster."""

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    first_name = models.CharField(max_length=PERSON_NAME_MAX_LENGTH)
    last_name = models.CharField(max_length=PERSON_NAME_MAX_LENGTH)
    jersey_number = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = TABLE_PLAYERS

    def __str__(self) -> str:
        number = f" #{self.jersey_number}" if self.jersey_number else ""
        return f"{self.first_name} {self.last_name}{number}"
