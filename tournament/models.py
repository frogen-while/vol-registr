from django.db import models

from .constants import (
    COURT_CHOICES,
    EMAIL_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    LEAGUE_LEVEL_CHOICES,
    LEAGUE_LEVEL_INDEPENDENT,
    LOGO_PATH_MAX_LENGTH,
    MATCH_SCHEDULED,
    MATCH_STATUS_CHOICES,
    MVP_TYPE_CHOICES,
    PAYMENT_ACCEPTED,
    PAYMENT_STATUS_CHOICES,
    PAYMENT_WAITING,
    PERSON_NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    POSITION_CHOICES,
    STAGE_CHOICES,
    TABLE_AUDIT_ENTRIES,
    TABLE_DREAM_TEAM,
    TABLE_GALLERY_PHOTOS,
    TABLE_GALLERY_VIDEOS,
    TABLE_GAME_SETS,
    TABLE_GROUP_STANDINGS,
    TABLE_MATCH_HIGHLIGHTS,
    TABLE_MATCHES,
    TABLE_PLAYER_MATCH_STATS,
    TABLE_PLAYERS,
    TABLE_TEAM_MATCH_STATS,
    TABLE_TEAMS,
    TABLE_MVP_SELECTIONS,
    TEAM_NAME_MAX_LENGTH,
    TEAM_STATUS_CHOICES,
    TEAM_STATUS_REGISTERED,
)


class Team(models.Model):
    """A registered tournament team with captain contact details."""

    name = models.CharField(
        max_length=TEAM_NAME_MAX_LENGTH, unique=True, verbose_name="Team Name"
    )
    logo_path = models.CharField(
        max_length=LOGO_PATH_MAX_LENGTH, blank=True, null=True
    )
    league_level = models.CharField(
        max_length=50, choices=LEAGUE_LEVEL_CHOICES, default=LEAGUE_LEVEL_INDEPENDENT
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
    blik_number = models.CharField(
        max_length=20, blank=True, default="", verbose_name="Assigned BLIK"
    )
    status = models.CharField(
        max_length=20, choices=TEAM_STATUS_CHOICES, default=TEAM_STATUS_REGISTERED,
        verbose_name="Registration Status",
    )
    checked_in = models.BooleanField(default=False, verbose_name="Checked In")
    roster_code = models.CharField(
        max_length=10, blank=True, default="", verbose_name="Roster Access Code",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = TABLE_TEAMS
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_payment_status_display()})"

    # ── Readiness indicators ─────────────────────────────

    @property
    def is_payment_ok(self) -> bool:
        """Payment accepted."""
        return self.payment_status == PAYMENT_ACCEPTED

    @property
    def is_roster_complete(self) -> bool:
        """At least 6 players on the roster."""
        return self.players.count() >= 6

    @property
    def is_contacts_complete(self) -> bool:
        """Captain email AND phone are filled."""
        return bool(self.cap_email) and bool(self.cap_phone)

    @property
    def is_logo_uploaded(self) -> bool:
        """Team logo path is not empty."""
        return bool(self.logo_path)

    @property
    def has_duplicate_jerseys(self) -> bool:
        """True if any two players share a non-empty jersey number."""
        numbers = list(
            self.players.exclude(jersey_number="")
            .values_list("jersey_number", flat=True)
        )
        return len(numbers) != len(set(numbers))

    @property
    def readiness_score(self) -> int:
        """0-5 score: payment + roster + contacts + logo + no-duplicate-jerseys."""
        return sum([
            self.is_payment_ok,
            self.is_roster_complete,
            self.is_contacts_complete,
            self.is_logo_uploaded,
            not self.has_duplicate_jerseys,
        ])


class Player(models.Model):
    """An individual player belonging to a team roster."""

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    first_name = models.CharField(max_length=PERSON_NAME_MAX_LENGTH)
    last_name = models.CharField(max_length=PERSON_NAME_MAX_LENGTH)
    jersey_number = models.CharField(max_length=3, blank=True, default="")
    position = models.CharField(
        max_length=3, choices=POSITION_CHOICES, blank=True, default="",
    )
    photo_path = models.CharField(
        max_length=LOGO_PATH_MAX_LENGTH, blank=True, default="",
    )

    class Meta:
        db_table = TABLE_PLAYERS

    def __str__(self) -> str:
        number = f" #{self.jersey_number}" if self.jersey_number != "" else ""
        return f"{self.first_name} {self.last_name}{number}"


# ── Match & Sets ─────────────────────────────────────────


class Match(models.Model):
    """A single tournament match between two teams."""

    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    group = models.CharField(max_length=1, blank=True, default="")
    court = models.IntegerField(choices=COURT_CHOICES)
    start_time = models.DateTimeField()
    team_a = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_as_home",
        null=True, blank=True,
    )
    team_b = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_as_away",
        null=True, blank=True,
    )
    score_a = models.IntegerField(default=0)
    score_b = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=MATCH_STATUS_CHOICES, default=MATCH_SCHEDULED
    )
    match_number = models.IntegerField(unique=True)
    stats_imported = models.BooleanField(default=False)
    stats_imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = TABLE_MATCHES
        ordering = ["start_time", "court"]
        verbose_name_plural = "Matches"

    def __str__(self) -> str:
        return f"M{self.match_number}: {self.team_a} vs {self.team_b}"

    @property
    def winner(self):
        if self.score_a > self.score_b:
            return self.team_a
        if self.score_b > self.score_a:
            return self.team_b
        return None

    @property
    def loser(self):
        if self.score_a > self.score_b:
            return self.team_b
        if self.score_b > self.score_a:
            return self.team_a
        return None

    @property
    def is_finished(self) -> bool:
        return self.status == "FINISHED"

    @property
    def set_scores_display(self) -> str:
        return f"{self.score_a}:{self.score_b}"


class GameSet(models.Model):
    """Individual set within a match."""

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="sets")
    set_number = models.PositiveIntegerField()
    score_a = models.PositiveIntegerField(default=0)
    score_b = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = TABLE_GAME_SETS
        ordering = ["set_number"]
        unique_together = [("match", "set_number")]

    def __str__(self) -> str:
        return f"Set {self.set_number}: {self.score_a}-{self.score_b}"


# ── Stats ────────────────────────────────────────────────


class PlayerMatchStats(models.Model):
    """Per-player statistics for a single match."""

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="player_stats")
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="match_stats")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="match_player_stats")
    position = models.CharField(max_length=5, choices=POSITION_CHOICES)
    jersey_number = models.CharField(max_length=3, default="")

    # Serve
    serve_attempts = models.PositiveIntegerField(default=0)
    aces = models.PositiveIntegerField(default=0)
    serve_errors = models.PositiveIntegerField(default=0)

    # Attack
    attack_attempts = models.PositiveIntegerField(default=0)
    kills = models.PositiveIntegerField(default=0)
    attack_errors = models.PositiveIntegerField(default=0)

    # Pass / Reception
    pass_attempts = models.PositiveIntegerField(default=0)
    perfect_passes = models.PositiveIntegerField(default=0)
    pass_errors = models.PositiveIntegerField(default=0)

    # Block / Set
    blocks = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    setting_errors = models.PositiveIntegerField(default=0)

    # Games (sets) played
    sets_played = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = TABLE_PLAYER_MATCH_STATS
        unique_together = [("match", "player")]

    def __str__(self) -> str:
        return f"{self.player} — M{self.match.match_number}"

    @property
    def points_won(self) -> int:
        return self.kills + self.aces + self.blocks

    @property
    def ace_pct(self):
        if not self.serve_attempts:
            return None
        return self.aces / self.serve_attempts * 100


class TeamMatchStats(models.Model):
    """Aggregated team-level statistics for a single match."""

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="team_stats")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="match_team_stats")

    serve_attempts = models.PositiveIntegerField(default=0)
    aces = models.PositiveIntegerField(default=0)
    serve_errors = models.PositiveIntegerField(default=0)

    attack_attempts = models.PositiveIntegerField(default=0)
    kills = models.PositiveIntegerField(default=0)
    attack_errors = models.PositiveIntegerField(default=0)

    pass_attempts = models.PositiveIntegerField(default=0)
    perfect_passes = models.PositiveIntegerField(default=0)
    pass_errors = models.PositiveIntegerField(default=0)

    blocks = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = TABLE_TEAM_MATCH_STATS
        unique_together = [("match", "team")]

    def __str__(self) -> str:
        return f"{self.team} — M{self.match.match_number}"


# ── Standings & Awards ───────────────────────────────────


class GroupStanding(models.Model):
    """Denormalized group-stage standings row (one per team)."""

    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name="standing")
    group = models.CharField(max_length=1)
    played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    sets_won = models.PositiveIntegerField(default=0)
    sets_lost = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    rank_in_group = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = TABLE_GROUP_STANDINGS
        ordering = ["group", "rank_in_group"]

    def __str__(self) -> str:
        return f"Group {self.group}: {self.team} (#{self.rank_in_group})"


class DreamTeamEntry(models.Model):
    """One of 7 Dream Team slots (best player per position)."""

    position = models.CharField(max_length=5, choices=POSITION_CHOICES)
    slot = models.CharField(max_length=20)
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="dream_team_entries")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    metric_label = models.CharField(max_length=50)
    metric_value = models.FloatField()
    is_auto = models.BooleanField(default=True)

    class Meta:
        db_table = TABLE_DREAM_TEAM

    def __str__(self) -> str:
        return f"{self.get_position_display()} — {self.player}"


class MVPSelection(models.Model):
    """Match or tournament MVP designation."""

    mvp_type = models.CharField(max_length=20, choices=MVP_TYPE_CHOICES)
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="mvp_selections")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True, default="")
    is_auto = models.BooleanField(default=True)

    class Meta:
        db_table = TABLE_MVP_SELECTIONS

    def __str__(self) -> str:
        return f"{self.get_mvp_type_display()}: {self.player}"


class MatchHighlight(models.Model):
    """Media highlight (video/photo) linked to a match or tournament-wide."""

    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name="highlights",
        null=True, blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    media_url = models.URLField(blank=True, default="")
    thumbnail_url = models.URLField(blank=True, default="")
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = TABLE_MATCH_HIGHLIGHTS
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


MEDIA_STATE_INCOMING = "incoming"
MEDIA_STATE_TAGGED = "tagged"
MEDIA_STATE_LINKED = "linked"
MEDIA_STATE_FEATURED = "featured"
MEDIA_STATE_CHOICES = [
    (MEDIA_STATE_INCOMING, "Incoming"),
    (MEDIA_STATE_TAGGED, "Tagged"),
    (MEDIA_STATE_LINKED, "Linked"),
    (MEDIA_STATE_FEATURED, "Featured"),
]


class GalleryPhoto(models.Model):
    """A photo stored on Google Drive, displayed in the site gallery."""

    title = models.CharField(max_length=200, blank=True, default="")
    drive_file_id = models.CharField(
        max_length=100, unique=True, verbose_name="Google Drive File ID",
    )
    drive_url = models.URLField(verbose_name="Google Drive URL")
    thumbnail_url = models.URLField(blank=True, default="", verbose_name="Thumbnail URL")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)
    media_state = models.CharField(
        max_length=20, choices=MEDIA_STATE_CHOICES, default=MEDIA_STATE_INCOMING,
    )
    match = models.ForeignKey(
        Match, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="gallery_photos",
    )
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="gallery_photos",
    )

    class Meta:
        db_table = TABLE_GALLERY_PHOTOS
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.title or f"Photo {self.drive_file_id[:8]}"


class GalleryVideo(models.Model):
    """A video stored on Google Drive, displayed in the site gallery."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    drive_file_id = models.CharField(
        max_length=100, unique=True, verbose_name="Google Drive File ID",
    )
    drive_url = models.URLField(verbose_name="Google Drive URL")
    thumbnail_url = models.URLField(blank=True, default="", verbose_name="Thumbnail URL")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)
    media_state = models.CharField(
        max_length=20, choices=MEDIA_STATE_CHOICES, default=MEDIA_STATE_INCOMING,
    )
    match = models.ForeignKey(
        Match, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="gallery_videos",
    )
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="gallery_videos",
    )

    class Meta:
        db_table = TABLE_GALLERY_VIDEOS
        ordering = ["order", "-uploaded_at"]

    def __str__(self) -> str:
        return self.title


# ── Audit ────────────────────────────────────────────────

AUDIT_CATEGORY_TEAM = "team"
AUDIT_CATEGORY_MATCH = "match"
AUDIT_CATEGORY_STATS = "stats"
AUDIT_CATEGORY_DREAMTEAM = "dreamteam"
AUDIT_CATEGORY_MEDIA = "media"
AUDIT_CATEGORY_CHECKIN = "checkin"

AUDIT_CATEGORY_CHOICES = [
    (AUDIT_CATEGORY_TEAM, "Team"),
    (AUDIT_CATEGORY_MATCH, "Match"),
    (AUDIT_CATEGORY_STATS, "Stats"),
    (AUDIT_CATEGORY_DREAMTEAM, "Dream Team"),
    (AUDIT_CATEGORY_MEDIA, "Media"),
    (AUDIT_CATEGORY_CHECKIN, "Check-in"),
]


class AuditEntry(models.Model):
    """Tracks key operational events for audit timeline."""

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True,
    )
    category = models.CharField(max_length=20, choices=AUDIT_CATEGORY_CHOICES, db_index=True)
    action = models.CharField(max_length=120)
    detail = models.TextField(blank=True, default="")
    entity_type = models.CharField(max_length=40, blank=True, default="")
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    entity_label = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        db_table = TABLE_AUDIT_ENTRIES
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action}"
