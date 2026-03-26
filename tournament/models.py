from django.db import models

from .constants import (
    CITY_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    LEAGUE_LEVEL_CHOICES,
    LEAGUE_LEVEL_INDEPENDENT,
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
    league_level = models.CharField(
        max_length=50, choices=LEAGUE_LEVEL_CHOICES, default=LEAGUE_LEVEL_INDEPENDENT
    )
    instagram = models.CharField(max_length=255, blank=True, null=True)
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
    cap_dob = models.DateField(null=True, blank=True, verbose_name="Captain Date of Birth")
    cap_jersey = models.IntegerField(null=True, blank=True, verbose_name="Captain Jersey Number")
    cap_email = models.EmailField(max_length=EMAIL_MAX_LENGTH, unique=True)
    cap_phone = models.CharField(
        max_length=PHONE_MAX_LENGTH, unique=True, blank=True, null=True
    )

    payment_status = models.IntegerField(
        choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_WAITING
    )
    blik_number = models.CharField(
        max_length=20, blank=True, default="", verbose_name="Assigned BLIK"
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
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        db_table = TABLE_PLAYERS

    def __str__(self) -> str:
        number = f" #{self.jersey_number}" if self.jersey_number else ""
        return f"{self.first_name} {self.last_name}{number}"


class Sector(models.Model):
    name = models.CharField(max_length=50, verbose_name="Sector Name")
    camera_urls = models.JSONField(blank=True, null=True, verbose_name="Camera RTSP URLs")

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectors"

    def __str__(self):
        return self.name


class Match(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Запланирован'),
        ('IN_PROGRESS', 'Идет'),
        ('FINISHED', 'Завершен'),
    )
    team_a = models.ForeignKey(Team, related_name='matches_as_a', on_delete=models.CASCADE)
    team_b = models.ForeignKey(Team, related_name='matches_as_b', on_delete=models.CASCADE)
    start_time = models.DateTimeField(blank=True, null=True, verbose_name="Match Start Time")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name="Status")
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sector")

    class Meta:
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.team_a.name} vs {self.team_b.name}"


class GameSet(models.Model):
    match = models.ForeignKey(Match, related_name='sets', on_delete=models.CASCADE)
    set_number = models.IntegerField(verbose_name="Set Number")
    score_a = models.IntegerField(default=0, verbose_name="Team A Score")
    score_b = models.IntegerField(default=0, verbose_name="Team B Score")
    is_completed = models.BooleanField(default=False, verbose_name="Is Completed")

    class Meta:
        ordering = ['set_number']
        verbose_name = "Game Set"
        verbose_name_plural = "Game Sets"

    def __str__(self):
        return f"{self.match} - Set {self.set_number}"


class MatchEvent(models.Model):
    CATEGORY_CHOICES = (
        ('ATTACK', 'Атака'), ('SET', 'Передача'), ('SERVE', 'Подача'),
        ('PASS', 'Прием'), ('DEF', 'Защита'), ('BLOCK', 'Блок'),
    )
    RESULT_CHOICES = (
        ('K', 'Kill (Очко)'), ('E', 'Error (Ошибка)'), ('TA', 'Attempt (В игре)'),
        ('A', 'Assist'), ('SA', 'Service Ace'), ('SE', 'Service Error'),
        ('RE', 'Reception Error'), ('DIG', 'Dig'), 
        ('BS', 'Block Solo'), ('BA', 'Block Assist'), ('BE', 'Block Error'),
    )

    match = models.ForeignKey(Match, related_name='events', on_delete=models.CASCADE)
    game_set = models.ForeignKey(GameSet, related_name='events', on_delete=models.CASCADE)
    
    # Who did the main action
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Initiating Team")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name="Initiating Player")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, verbose_name="Action Category")
    result = models.CharField(max_length=5, choices=RESULT_CHOICES, verbose_name="Action Result")
    
    # Follow-up: Who was affected (e.g. who got blocked, who made reception error)
    affected_player = models.ForeignKey(Player, related_name='affected_events', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Affected Player")

    # State tracking
    score_a_at_time = models.IntegerField(default=0)
    score_b_at_time = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Match Event"
        verbose_name_plural = "Match Events"

    def __str__(self):
        return f"Set {self.game_set.set_number}: {self.player} ({self.get_result_display()})"
