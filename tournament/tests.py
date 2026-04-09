import io

from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from .constants import (
    MATCH_FINISHED,
    MATCH_SCHEDULED,
    STAGE_GROUP,
    STAGE_QF,
    TEAM_STATUS_APPROVED,
    TEAM_STATUS_AWAITING_PAYMENT,
    TEAM_STATUS_PAID,
    TEAM_STATUS_REGISTERED,
)
from .models import (
    DreamTeamEntry,
    GalleryPhoto,
    GalleryVideo,
    GameSet,
    GroupStanding,
    Match,
    MatchHighlight,
    MVPSelection,
    Player,
    PlayerMatchStats,
    Team,
    TeamMatchStats,
)


# ── Helpers ──────────────────────────────────────────────


def _make_team(name, group="A", **kw):
    defaults = dict(
        cap_name="Cap",
        cap_surname="Test",
        cap_email=f"{name.replace(' ', '_').lower()}@test.com",
        group_name=group,
    )
    defaults.update(kw)
    return Team.objects.create(name=name, **defaults)


def _make_players(team, count=6, start_jersey=1):
    players = []
    for i in range(start_jersey, start_jersey + count):
        players.append(
            Player.objects.create(
                team=team,
                first_name=f"Player{i}",
                last_name=team.name.split()[0],
                jersey_number=i,

            )
        )
    return players


def _make_match(team_a, team_b, number=1, stage=STAGE_GROUP, **kw):
    defaults = dict(
        court=1,
        start_time=timezone.now(),
        status=MATCH_SCHEDULED,
        match_number=number,
    )
    defaults.update(kw)
    return Match.objects.create(
        stage=stage,
        group=team_a.group_name or "",
        team_a=team_a,
        team_b=team_b,
        **defaults,
    )


def _csv_header():
    return "Player Name,Player Number,Position,Serve Attempts,Aces,Serve Errors,Attack Attempts,Kills,Attack Errors,Pass Attempts,3-pass,Total Pass Errors,Blocks,Assists,Setting Errors"


def _csv_row(name, jersey, pos="OH", sa=5, aces=1, se=0, aa=10, kills=4,
             ae=1, pa=8, pp=3, pe=1, blocks=1, assists=0, seterr=0):
    return f"{name},{jersey},{pos},{sa},{aces},{se},{aa},{kills},{ae},{pa},{pp},{pe},{blocks},{assists},{seterr}"


def _build_csv(rows):
    lines = [_csv_header()] + rows
    return io.BytesIO(("\n".join(lines)).encode("utf-8"))


# ══════════════════════════════════════════════════════════
# 16.1 — Unit tests for models
# ══════════════════════════════════════════════════════════


class TestMatch(TestCase):
    def setUp(self):
        self.team_a = _make_team("Alpha", group="A")
        self.team_b = _make_team("Beta", group="A")

    def test_create_match(self):
        m = _make_match(self.team_a, self.team_b)
        self.assertEqual(m.team_a, self.team_a)
        self.assertEqual(m.team_b, self.team_b)
        self.assertEqual(m.status, MATCH_SCHEDULED)

    def test_winner_team_a(self):
        m = _make_match(self.team_a, self.team_b, score_a=2, score_b=1)
        self.assertEqual(m.winner, self.team_a)
        self.assertEqual(m.loser, self.team_b)

    def test_winner_team_b(self):
        m = _make_match(self.team_a, self.team_b, score_a=0, score_b=2)
        self.assertEqual(m.winner, self.team_b)
        self.assertEqual(m.loser, self.team_a)

    def test_winner_draw_returns_none(self):
        m = _make_match(self.team_a, self.team_b, score_a=1, score_b=1)
        self.assertIsNone(m.winner)
        self.assertIsNone(m.loser)

    def test_is_finished_true(self):
        m = _make_match(self.team_a, self.team_b, status=MATCH_FINISHED)
        self.assertTrue(m.is_finished)

    def test_is_finished_false(self):
        m = _make_match(self.team_a, self.team_b, status=MATCH_SCHEDULED)
        self.assertFalse(m.is_finished)

    def test_set_scores_display(self):
        m = _make_match(self.team_a, self.team_b, score_a=2, score_b=1)
        self.assertEqual(m.set_scores_display, "2:1")


class TestPlayerMatchStats(TestCase):
    def setUp(self):
        self.team = _make_team("Gamma")
        self.player = Player.objects.create(
            team=self.team, first_name="Jane", last_name="Doe", jersey_number=7,
        )
        self.match = _make_match(self.team, _make_team("Delta"), number=1)

    def _create_stats(self, **kw):
        defaults = dict(
            match=self.match, player=self.player, team=self.team,
            position="OH", jersey_number=7,
        )
        defaults.update(kw)
        return PlayerMatchStats.objects.create(**defaults)

    def test_points_won(self):
        s = self._create_stats(kills=5, aces=2, blocks=3)
        self.assertEqual(s.points_won, 10)

    def test_attack_efficiency(self):
        s = self._create_stats(kills=10, attack_errors=3, attack_attempts=20)
        # (10 - 3) / 20 * 100 = 35.0
        self.assertAlmostEqual(s.attack_efficiency, 35.0)

    def test_attack_efficiency_zero_attempts(self):
        s = self._create_stats(kills=0, attack_errors=0, attack_attempts=0)
        self.assertIsNone(s.attack_efficiency)

    def test_ace_pct(self):
        s = self._create_stats(aces=3, serve_attempts=10)
        self.assertAlmostEqual(s.ace_pct, 30.0)

    def test_ace_pct_zero_attempts(self):
        s = self._create_stats(aces=0, serve_attempts=0)
        self.assertIsNone(s.ace_pct)

    def test_pass_3_pct(self):
        s = self._create_stats(perfect_passes=6, pass_attempts=10)
        self.assertAlmostEqual(s.pass_3_pct, 60.0)

    def test_pass_3_pct_zero_attempts(self):
        s = self._create_stats(perfect_passes=0, pass_attempts=0)
        self.assertIsNone(s.pass_3_pct)


class TestGroupStanding(TestCase):
    def test_sorting_by_points(self):
        t1 = _make_team("First", group="A")
        t2 = _make_team("Second", group="A")
        t3 = _make_team("Third", group="A")
        GroupStanding.objects.create(team=t1, group="A", points=6, wins=2, rank_in_group=1)
        GroupStanding.objects.create(team=t2, group="A", points=3, wins=1, rank_in_group=2)
        GroupStanding.objects.create(team=t3, group="A", points=0, wins=0, rank_in_group=3)

        standings = list(GroupStanding.objects.filter(group="A").order_by("-points"))
        self.assertEqual(standings[0].team, t1)
        self.assertEqual(standings[1].team, t2)
        self.assertEqual(standings[2].team, t3)


# ══════════════════════════════════════════════════════════
# 16.2 — Tests for CSV import
# ══════════════════════════════════════════════════════════


class TestCSVParse(TestCase):
    def test_parse_valid_csv(self):
        from .csv_import import parse_csv

        rows = [
            _csv_row(f"Player{i} Team", i, pos="OH")
            for i in range(1, 13)
        ]
        csv_file = _build_csv(rows)
        result = parse_csv(csv_file)

        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(len(result["rows"]), 12)

    def test_parse_csv_missing_columns(self):
        from .csv_import import parse_csv

        csv_file = io.BytesIO(b"Name,Number\nJohn,1\n")
        result = parse_csv(csv_file)

        self.assertGreater(len(result["errors"]), 0)
        self.assertIn("Missing required columns", result["errors"][0])

    def test_parse_csv_invalid_numbers(self):
        from .csv_import import parse_csv

        row = _csv_row("Bad Player", 1, kills=-5)
        csv_file = _build_csv([row])
        result = parse_csv(csv_file)

        self.assertGreater(len(result["errors"]), 0)
        self.assertTrue(any("negative" in e for e in result["errors"]))


class TestCSVMultiSection(TestCase):
    """Test parsing of real SoloStats multi-section CSV format."""

    MULTI_CSV = (
        "Player Number, Player Name, Serve Attempts, Aces, Serve Errors, Pass Attempts, 3-pass, Total Pass Errors\n"
        "1, Alice, 6, 2, 4, 5, 0, 4\n"
        "10, Bob, 7, 0, 0, 1, 0, 1\n"
        "undefined, (team), 0, 0, 0, 0, 0, 0\n"
        "Total, , 13, 2, 4, 6, 0, 5\n"
        "\n"
        "Player Number, Player Name, Attack Attempts, Attack Errors, Kills\n"
        "1, Alice, 6, 2, 4\n"
        "10, Bob, 6, 2, 4\n"
        "undefined, (team), 1, 0, 1\n"
        "Total, , 13, 4, 9\n"
        "\n"
        "Player Number, Player Name, Blocks, Assists, Setting Errors\n"
        "1, Alice, 3, 0, 0\n"
        "10, Bob, 0, 5, 1\n"
        "undefined, (team), 0, 0, 0\n"
        "Total, , 3, 5, 1\n"
    )

    def test_multi_section_merges_by_player_number(self):
        from .csv_import import parse_csv
        result = parse_csv(io.BytesIO(self.MULTI_CSV.encode("utf-8")))

        self.assertEqual(len(result["errors"]), 0, result["errors"])
        self.assertEqual(len(result["rows"]), 2)

        by_jersey = {r["jersey_number"]: r for r in result["rows"]}
        alice = by_jersey["1"]
        self.assertEqual(alice["aces"], 2)
        self.assertEqual(alice["kills"], 4)
        self.assertEqual(alice["blocks"], 3)
        self.assertEqual(alice["perfect_passes"], 0)
        self.assertEqual(alice["pass_errors"], 4)

        bob = by_jersey["10"]
        self.assertEqual(bob["assists"], 5)
        self.assertEqual(bob["attack_attempts"], 6)
        self.assertEqual(bob["setting_errors"], 1)

    def test_total_and_team_rows_skipped(self):
        from .csv_import import parse_csv
        result = parse_csv(io.BytesIO(self.MULTI_CSV.encode("utf-8")))

        self.assertEqual(len(result["rows"]), 2)
        names = {r["player_name"] for r in result["rows"]}
        self.assertNotIn("(team)", names)

    def test_dash_values_treated_as_zero(self):
        from .csv_import import parse_csv
        csv_text = (
            "Player Number, Player Name, Aces, Kills, Blocks\n"
            "5, Charlie, -, 3, -\n"
        )
        result = parse_csv(io.BytesIO(csv_text.encode("utf-8")))
        self.assertEqual(len(result["errors"]), 0, result["errors"])
        self.assertEqual(result["rows"][0]["aces"], 0)
        self.assertEqual(result["rows"][0]["blocks"], 0)

    def test_legacy_single_section_still_works(self):
        from .csv_import import parse_csv
        csv_file = _build_csv([
            _csv_row(f"Player{i} Team", i, pos="OH") for i in range(1, 4)
        ])
        result = parse_csv(csv_file)
        self.assertEqual(len(result["errors"]), 0, result["errors"])
        self.assertEqual(len(result["rows"]), 3)


class TestCSVImport(TestCase):
    def setUp(self):
        self.team_a = _make_team("Aces", group="A")
        self.team_b = _make_team("Kings", group="A")
        self.players_a = _make_players(self.team_a, 6, start_jersey=1)
        self.players_b = _make_players(self.team_b, 6, start_jersey=11)
        self.match = _make_match(self.team_a, self.team_b, number=1)

    def _csv_for_match(self):
        rows = []
        for p in self.players_a:
            rows.append(
                _csv_row(f"{p.first_name} {p.last_name}", p.jersey_number, pos="OH",
                         sa=5, aces=1, se=0, aa=10, kills=4, ae=1,
                         pa=8, pp=3, pe=1, blocks=1, assists=0, seterr=0)
            )
        for p in self.players_b:
            rows.append(
                _csv_row(f"{p.first_name} {p.last_name}", p.jersey_number, pos="MB",
                         sa=4, aces=0, se=1, aa=8, kills=3, ae=2,
                         pa=6, pp=2, pe=2, blocks=2, assists=1, seterr=0)
            )
        return _build_csv(rows)

    def test_preview_no_commit(self):
        from .services import preview_csv_import

        csv_file = self._csv_for_match()
        result = preview_csv_import(csv_file, self.match.pk)

        self.assertTrue(result["can_import"])
        self.assertEqual(PlayerMatchStats.objects.count(), 0)

    def test_confirm_creates_stats(self):
        from .services import confirm_csv_import

        csv_file = self._csv_for_match()
        result = confirm_csv_import(csv_file, self.match.pk)

        self.assertEqual(result["imported"], 12)
        self.assertEqual(PlayerMatchStats.objects.filter(match=self.match).count(), 12)
        self.match.refresh_from_db()
        self.assertTrue(self.match.stats_imported)
        self.assertEqual(self.match.status, MATCH_FINISHED)

    def test_confirm_overwrites(self):
        from .services import confirm_csv_import

        csv_file_1 = self._csv_for_match()
        confirm_csv_import(csv_file_1, self.match.pk)
        self.assertEqual(PlayerMatchStats.objects.filter(match=self.match).count(), 12)

        csv_file_2 = self._csv_for_match()
        confirm_csv_import(csv_file_2, self.match.pk)
        self.assertEqual(PlayerMatchStats.objects.filter(match=self.match).count(), 12)

    def test_recalculate_standings_after_import(self):
        from .services import confirm_csv_import

        GroupStanding.objects.create(
            team=self.team_a, group="A", played=0, wins=0, losses=0,
            sets_won=0, sets_lost=0, points=0, rank_in_group=1,
        )
        GroupStanding.objects.create(
            team=self.team_b, group="A", played=0, wins=0, losses=0,
            sets_won=0, sets_lost=0, points=0, rank_in_group=2,
        )

        self.match.score_a = 2
        self.match.score_b = 0
        self.match.save()

        csv_file = self._csv_for_match()
        confirm_csv_import(csv_file, self.match.pk)

        gs_a = GroupStanding.objects.get(team=self.team_a)
        gs_b = GroupStanding.objects.get(team=self.team_b)

        self.assertEqual(gs_a.played, 1)
        self.assertEqual(gs_a.wins, 1)
        self.assertEqual(gs_a.points, 3)  # 2-0 win = 3 pts

        self.assertEqual(gs_b.played, 1)
        self.assertEqual(gs_b.losses, 1)
        self.assertEqual(gs_b.points, 0)  # 0-2 loss = 0 pts


class TestCSVTeamScopedImport(TestCase):
    """Test per-team stats import (Option 2)."""

    def setUp(self):
        self.team_a = _make_team("Aces", group="A")
        self.team_b = _make_team("Kings", group="A")
        self.players_a = _make_players(self.team_a, 6, start_jersey=1)
        self.players_b = _make_players(self.team_b, 6, start_jersey=11)
        self.match = _make_match(self.team_a, self.team_b, number=1)

    def _csv_for_team(self, players):
        rows = []
        for p in players:
            rows.append(
                _csv_row(f"{p.first_name} {p.last_name}", p.jersey_number, pos="OH",
                         sa=5, aces=1, se=0, aa=10, kills=4, ae=1,
                         pa=8, pp=3, pe=1, blocks=1, assists=0, seterr=0)
            )
        return _build_csv(rows)

    def test_import_team_a_only(self):
        from .services import confirm_csv_import

        csv_a = self._csv_for_team(self.players_a)
        result = confirm_csv_import(csv_a, self.match.pk, self.team_a.pk)

        self.assertEqual(result["imported"], 6)
        self.assertEqual(
            PlayerMatchStats.objects.filter(match=self.match, team=self.team_a).count(), 6
        )
        self.assertEqual(
            PlayerMatchStats.objects.filter(match=self.match, team=self.team_b).count(), 0
        )
        # Match NOT marked as fully imported yet
        self.match.refresh_from_db()
        self.assertFalse(self.match.stats_imported)
        self.assertEqual(self.match.status, MATCH_SCHEDULED)

    def test_import_both_teams_sequentially(self):
        from .services import confirm_csv_import

        csv_a = self._csv_for_team(self.players_a)
        confirm_csv_import(csv_a, self.match.pk, self.team_a.pk)

        csv_b = self._csv_for_team(self.players_b)
        confirm_csv_import(csv_b, self.match.pk, self.team_b.pk)

        self.assertEqual(
            PlayerMatchStats.objects.filter(match=self.match).count(), 12
        )
        # NOW match is fully imported
        self.match.refresh_from_db()
        self.assertTrue(self.match.stats_imported)
        self.assertEqual(self.match.status, MATCH_FINISHED)

    def test_reimport_does_not_delete_other_team(self):
        from .services import confirm_csv_import

        csv_a = self._csv_for_team(self.players_a)
        confirm_csv_import(csv_a, self.match.pk, self.team_a.pk)

        csv_b = self._csv_for_team(self.players_b)
        confirm_csv_import(csv_b, self.match.pk, self.team_b.pk)

        # Re-import team A — team B must stay
        csv_a2 = self._csv_for_team(self.players_a)
        confirm_csv_import(csv_a2, self.match.pk, self.team_a.pk)

        self.assertEqual(
            PlayerMatchStats.objects.filter(match=self.match, team=self.team_a).count(), 6
        )
        self.assertEqual(
            PlayerMatchStats.objects.filter(match=self.match, team=self.team_b).count(), 6
        )

    def test_team_match_stats_per_team(self):
        from .services import confirm_csv_import

        csv_a = self._csv_for_team(self.players_a)
        confirm_csv_import(csv_a, self.match.pk, self.team_a.pk)
        self.assertEqual(
            TeamMatchStats.objects.filter(match=self.match, team=self.team_a).count(), 1
        )
        self.assertEqual(
            TeamMatchStats.objects.filter(match=self.match, team=self.team_b).count(), 0
        )

        csv_b = self._csv_for_team(self.players_b)
        confirm_csv_import(csv_b, self.match.pk, self.team_b.pk)
        self.assertEqual(
            TeamMatchStats.objects.filter(match=self.match, team=self.team_b).count(), 1
        )

    def test_preview_team_scoped(self):
        from .services import preview_csv_import

        csv_a = self._csv_for_team(self.players_a)
        result = preview_csv_import(csv_a, self.match.pk, self.team_a.pk)

        self.assertTrue(result["can_import"])
        self.assertEqual(len(result["preview"]), 6)
        # All matched players belong to team_a
        for row in result["preview"]:
            self.assertEqual(row["_team_id"], self.team_a.pk)

    def test_wrong_team_csv_gives_warnings(self):
        """Uploading team B's CSV while selecting team A → all unmatched."""
        from .services import preview_csv_import

        csv_b = self._csv_for_team(self.players_b)
        result = preview_csv_import(csv_b, self.match.pk, self.team_a.pk)

        # All players unmatched (jersey 11-16 not in team A roster 1-6)
        self.assertFalse(result["can_import"])


# ══════════════════════════════════════════════════════════
# 16.3 — Smoke tests for views
# ══════════════════════════════════════════════════════════


_STATIC_OVERRIDE = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestDemoViewsSmoke(TestCase):
    """All demo/preview URLs should return 200 even with an empty DB."""

    def setUp(self):
        self.client = Client()

    def test_tournament_hub(self):
        r = self.client.get(reverse("tournament_hub"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "sp-page")

    def test_tournament_demo(self):
        r = self.client.get(reverse("tournament_demo"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Coming Soon")
        self.assertContains(r, "cs-countdown")

    def test_tournament_teams(self):
        r = self.client.get(reverse("tournament_teams"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "sp-page")

    def test_tournament_dream_team(self):
        r = self.client.get(reverse("tournament_dream_team"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "sp-page")


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestDBViewsSmoke(TestCase):
    """DB-backed views with seed data should return 200."""

    @classmethod
    def setUpTestData(cls):
        cls.team_a = _make_team("Smoke Alpha", group="A")
        cls.team_b = _make_team("Smoke Beta", group="A")
        cls.players_a = _make_players(cls.team_a, 6, start_jersey=1)
        cls.players_b = _make_players(cls.team_b, 6, start_jersey=11)
        cls.match = _make_match(cls.team_a, cls.team_b, number=1,
                                status=MATCH_FINISHED, score_a=2, score_b=1)
        GameSet.objects.create(match=cls.match, set_number=1, score_a=25, score_b=20)
        GameSet.objects.create(match=cls.match, set_number=2, score_a=20, score_b=25)
        GameSet.objects.create(match=cls.match, set_number=3, score_a=15, score_b=10)
        for p in cls.players_a:
            PlayerMatchStats.objects.create(
                match=cls.match, player=p, team=cls.team_a,
                position="OH", jersey_number=p.jersey_number,
                kills=4, aces=1, blocks=1, attack_attempts=10,
                serve_attempts=5, pass_attempts=8, perfect_passes=3,
            )
        for p in cls.players_b:
            PlayerMatchStats.objects.create(
                match=cls.match, player=p, team=cls.team_b,
                position="MB", jersey_number=p.jersey_number,
                kills=3, aces=0, blocks=2, attack_attempts=8,
                serve_attempts=4, pass_attempts=6, perfect_passes=2,
            )

    def test_match_detail(self):
        r = self.client.get(reverse("tournament_match", args=[self.match.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Smoke Alpha")
        self.assertContains(r, "Smoke Beta")

    def test_team_stats(self):
        r = self.client.get(reverse("tournament_team", args=[self.team_a.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Smoke Alpha")

    def test_player_detail(self):
        player = self.players_a[0]
        r = self.client.get(reverse("tournament_player", args=[player.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, player.first_name)

    def test_match_detail_nonexistent_returns_404(self):
        r = self.client.get(reverse("tournament_match", args=[9999]))
        self.assertEqual(r.status_code, 404)

    def test_tournament_demo_coming_soon(self):
        r = self.client.get(reverse("tournament_demo"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Coming Soon")
        self.assertContains(r, "cs-countdown")

    def test_hub_accessible(self):
        r = self.client.get(reverse("tournament_hub"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Tournament Hub")

    def test_team_stats_nonexistent_returns_404(self):
        r = self.client.get(reverse("tournament_team", args=[9999]))
        self.assertEqual(r.status_code, 404)

    def test_player_detail_nonexistent_returns_404(self):
        r = self.client.get(reverse("tournament_player", args=[9999]))
        self.assertEqual(r.status_code, 404)


# ══════════════════════════════════════════════════════════
# Phase 17 — Admin Panel Tests
# ══════════════════════════════════════════════════════════


def _staff_client():
    """Return a Client logged in as a staff user."""
    user = User.objects.create_user("staff", "s@t.com", "pass1234", is_staff=True)
    c = Client()
    c.login(username="staff", password="pass1234")
    return c


# ── 17.1 Auth tests ──────────────────────────────────────


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelAuth(TestCase):
    """Anonymous users are redirected; staff users get 200."""

    def test_anon_redirect_dashboard(self):
        r = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/panel/login/", r.url)

    def test_anon_redirect_teams(self):
        r = self.client.get(reverse("panel:teams"))
        self.assertEqual(r.status_code, 302)

    def test_anon_redirect_schedule(self):
        r = self.client.get(reverse("panel:schedule"))
        self.assertEqual(r.status_code, 302)

    def test_anon_redirect_dreamteam(self):
        r = self.client.get(reverse("panel:dreamteam"))
        self.assertEqual(r.status_code, 302)

    def test_login_page_loads(self):
        r = self.client.get(reverse("panel:login"))
        self.assertEqual(r.status_code, 200)

    def test_login_valid_staff(self):
        User.objects.create_user("staffu", "s@e.com", "pw1234", is_staff=True)
        r = self.client.post(reverse("panel:login"), {
            "username": "staffu", "password": "pw1234",
        })
        self.assertEqual(r.status_code, 302)

    def test_login_invalid_credentials(self):
        r = self.client.post(reverse("panel:login"), {
            "username": "none", "password": "none",
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Invalid")

    def test_logout_redirects(self):
        _staff_client()
        r = self.client.get(reverse("panel:logout"))
        self.assertEqual(r.status_code, 302)


# ── 17.2 Panel GET smoke tests ───────────────────────────


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelGETSmoke(TestCase):
    """All panel GET pages return 200 for authenticated staff."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("st", "s@t.com", "pw", is_staff=True)
        cls.team_a = _make_team("PanelAlpha", group="A", status=TEAM_STATUS_APPROVED)
        cls.team_b = _make_team("PanelBeta", group="A", status=TEAM_STATUS_APPROVED)
        cls.players_a = _make_players(cls.team_a, 6, start_jersey=1)
        cls.match = _make_match(cls.team_a, cls.team_b, number=1,
                                status=MATCH_FINISHED, score_a=2, score_b=1)
        for p in cls.players_a:
            PlayerMatchStats.objects.create(
                match=cls.match, player=p, team=cls.team_a,
                position="OH", jersey_number=p.jersey_number,
                kills=4, aces=1, blocks=1, attack_attempts=10,
                serve_attempts=5, pass_attempts=8, perfect_passes=3,
            )

    def setUp(self):
        self.client.login(username="st", password="pw")

    def test_dashboard(self):
        r = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(r.status_code, 200)

    def test_teams_list(self):
        r = self.client.get(reverse("panel:teams"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "PanelAlpha")

    def test_team_detail(self):
        r = self.client.get(reverse("panel:team_detail", args=[self.team_a.pk]))
        self.assertEqual(r.status_code, 200)

    def test_team_create_form(self):
        r = self.client.get(reverse("panel:team_create"))
        self.assertEqual(r.status_code, 200)

    def test_team_edit_form(self):
        r = self.client.get(reverse("panel:team_edit", args=[self.team_a.pk]))
        self.assertEqual(r.status_code, 200)

    def test_checkin(self):
        r = self.client.get(reverse("panel:checkin"))
        self.assertEqual(r.status_code, 200)

    def test_schedule_list(self):
        r = self.client.get(reverse("panel:schedule"))
        self.assertEqual(r.status_code, 200)

    def test_match_create_form(self):
        r = self.client.get(reverse("panel:match_create"))
        self.assertEqual(r.status_code, 200)

    def test_match_edit_form(self):
        r = self.client.get(reverse("panel:match_edit", args=[self.match.pk]))
        self.assertEqual(r.status_code, 200)

    def test_stats_list(self):
        r = self.client.get(reverse("panel:stats"))
        self.assertEqual(r.status_code, 200)

    def test_stats_detail(self):
        r = self.client.get(reverse("panel:stats_detail", args=[self.match.pk]))
        self.assertEqual(r.status_code, 200)

    def test_stats_edit(self):
        r = self.client.get(reverse("panel:stats_edit", args=[self.match.pk]))
        self.assertEqual(r.status_code, 200)

    def test_stats_import(self):
        r = self.client.get(reverse("panel:stats_import", args=[self.match.pk]))
        self.assertEqual(r.status_code, 200)

    def test_gallery_list(self):
        r = self.client.get(reverse("panel:gallery"))
        self.assertEqual(r.status_code, 200)

    def test_gallery_photos_tab(self):
        r = self.client.get(reverse("panel:gallery") + "?tab=photos")
        self.assertEqual(r.status_code, 200)

    def test_gallery_videos_tab(self):
        r = self.client.get(reverse("panel:gallery") + "?tab=videos")
        self.assertEqual(r.status_code, 200)

    def test_gallery_add_form(self):
        r = self.client.get(reverse("panel:gallery_add"))
        self.assertEqual(r.status_code, 200)

    def test_video_add_form(self):
        r = self.client.get(reverse("panel:video_add"))
        self.assertEqual(r.status_code, 200)

    def test_schedule_csv_import(self):
        r = self.client.get(reverse("panel:schedule_csv_import"))
        self.assertEqual(r.status_code, 200)

    def test_dreamteam(self):
        r = self.client.get(reverse("panel:dreamteam"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "pnl-dt-court")


# ── 17.3 Team CRUD tests ────────────────────────────────


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelTeamCRUD(TestCase):
    """Create, edit, delete team through the panel."""

    def setUp(self):
        self.user = User.objects.create_user("st", "s@t.com", "pw", is_staff=True)
        self.client.login(username="st", password="pw")

    def test_create_team(self):
        data = {
            "name": "NewTeam",
            "cap_name": "Cap",
            "cap_surname": "Sur",
            "cap_email": "new@team.com",
            "league_level": "independent",
            "payment_status": 0,
            "status": TEAM_STATUS_REGISTERED,
            # PlayerInlineFormSet management data
            "players-TOTAL_FORMS": "0",
            "players-INITIAL_FORMS": "0",
            "players-MIN_NUM_FORMS": "0",
            "players-MAX_NUM_FORMS": "1000",
        }
        r = self.client.post(reverse("panel:team_create"), data)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Team.objects.filter(name="NewTeam").exists())

    def test_edit_team(self):
        team = _make_team("EditMe")
        data = {
            "name": "EditedName",
            "cap_name": team.cap_name,
            "cap_surname": team.cap_surname,
            "cap_email": team.cap_email,
            "league_level": "independent",
            "payment_status": 0,
            "status": TEAM_STATUS_REGISTERED,
            "players-TOTAL_FORMS": "0",
            "players-INITIAL_FORMS": "0",
            "players-MIN_NUM_FORMS": "0",
            "players-MAX_NUM_FORMS": "1000",
        }
        r = self.client.post(reverse("panel:team_edit", args=[team.pk]), data)
        self.assertEqual(r.status_code, 302)
        team.refresh_from_db()
        self.assertEqual(team.name, "EditedName")

    def test_delete_team(self):
        team = _make_team("DeleteMe")
        r = self.client.post(reverse("panel:team_delete", args=[team.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Team.objects.filter(pk=team.pk).exists())


# ── 17.4 Team status workflow ────────────────────────────


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelStatusWorkflow(TestCase):
    """Team status transitions follow the allowed workflow."""

    def setUp(self):
        self.user = User.objects.create_user("st", "s@t.com", "pw", is_staff=True)
        self.client.login(username="st", password="pw")
        self.team = _make_team("StatusTeam", status=TEAM_STATUS_REGISTERED)

    def test_valid_transition(self):
        r = self.client.post(
            reverse("panel:team_status", args=[self.team.pk]),
            {"new_status": TEAM_STATUS_AWAITING_PAYMENT},
        )
        self.assertEqual(r.status_code, 302)
        self.team.refresh_from_db()
        self.assertEqual(self.team.status, TEAM_STATUS_AWAITING_PAYMENT)

    def test_invalid_transition_blocked(self):
        r = self.client.post(
            reverse("panel:team_status", args=[self.team.pk]),
            {"new_status": TEAM_STATUS_APPROVED},
        )
        self.assertEqual(r.status_code, 302)
        self.team.refresh_from_db()
        self.assertEqual(self.team.status, TEAM_STATUS_REGISTERED)

    def test_full_workflow(self):
        transitions = [
            TEAM_STATUS_AWAITING_PAYMENT,
            TEAM_STATUS_PAID,
            TEAM_STATUS_APPROVED,
        ]
        for new_status in transitions:
            self.client.post(
                reverse("panel:team_status", args=[self.team.pk]),
                {"new_status": new_status},
            )
        self.team.refresh_from_db()
        self.assertEqual(self.team.status, TEAM_STATUS_APPROVED)

    def test_batch_action(self):
        t2 = _make_team("BatchTeam")
        self.client.post(reverse("panel:team_batch"), {
            "batch_action": "reset",
            "team_ids": [self.team.pk, t2.pk],
        })
        self.team.refresh_from_db()
        t2.refresh_from_db()
        self.assertEqual(self.team.status, TEAM_STATUS_REGISTERED)
        self.assertEqual(t2.status, TEAM_STATUS_REGISTERED)


# ── 17.5 Check-in toggle ────────────────────────────────


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelCheckin(TestCase):
    """Check-in AJAX toggle for approved teams."""

    def setUp(self):
        self.user = User.objects.create_user("st", "s@t.com", "pw", is_staff=True)
        self.client.login(username="st", password="pw")
        self.team = _make_team("CITeam", status=TEAM_STATUS_APPROVED)

    def test_toggle_on(self):
        r = self.client.post(reverse("panel:checkin_toggle", args=[self.team.pk]))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["checked_in"])

    def test_toggle_off(self):
        self.team.checked_in = True
        self.team.save()
        r = self.client.post(reverse("panel:checkin_toggle", args=[self.team.pk]))
        data = r.json()
        self.assertFalse(data["checked_in"])

    def test_toggle_non_approved_404(self):
        team2 = _make_team("NonApp", status=TEAM_STATUS_REGISTERED)
        r = self.client.post(reverse("panel:checkin_toggle", args=[team2.pk]))
        self.assertEqual(r.status_code, 404)


# ── 17.5b CSV Schedule Import ────────────────────────────


def _schedule_csv_bytes(rows_text):
    """Wrap CSV text in a BytesIO for upload."""
    return io.BytesIO(rows_text.encode("utf-8"))


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelScheduleCSV(TestCase):
    """Upload, preview, and confirm schedule CSV import."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("st", "s@t.com", "pw", is_staff=True)
        cls.team_a = _make_team("AlphaCSV", group="A")
        cls.team_b = _make_team("BetaCSV", group="A")

    def setUp(self):
        self.client.login(username="st", password="pw")
        self.url = reverse("panel:schedule_csv_import")

    def _upload(self, csv_text):
        f = _schedule_csv_bytes(csv_text)
        f.name = "schedule.csv"
        return self.client.post(self.url, {"csv_file": f})

    def test_get_page(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_upload_valid_csv_shows_preview(self):
        csv_text = (
            "Time,Team A,Team B,Group,Court,Stage\n"
            "2026-06-01 10:00,AlphaCSV,BetaCSV,A,1,GROUP\n"
        )
        r = self._upload(csv_text)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["preview"])
        self.assertEqual(len(r.context["preview"]), 1)

    def test_upload_and_confirm_creates_matches(self):
        csv_text = (
            "Time,Team A,Team B,Group,Court,Stage\n"
            "2026-06-01 10:00,AlphaCSV,BetaCSV,A,1,GROUP\n"
        )
        # Step 1: Upload → preview
        self._upload(csv_text)
        # Step 2: Confirm
        r = self.client.post(self.url, {"confirm": "1"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Match.objects.filter(team_a=self.team_a, team_b=self.team_b).count(), 1)
        m = Match.objects.get(team_a=self.team_a, team_b=self.team_b)
        self.assertEqual(m.court, 1)
        self.assertEqual(m.stage, STAGE_GROUP)

    def test_upload_unknown_team_returns_errors(self):
        csv_text = (
            "Time,Team A,Team B,Group,Court\n"
            "2026-06-01 10:00,NoSuchTeam,BetaCSV,A,1\n"
        )
        r = self._upload(csv_text)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["csv_errors"])
        self.assertIn("not found", r.context["csv_errors"][0])

    def test_upload_invalid_court_returns_errors(self):
        csv_text = (
            "Time,Team A,Team B,Group,Court\n"
            "2026-06-01 10:00,AlphaCSV,BetaCSV,A,9\n"
        )
        r = self._upload(csv_text)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["csv_errors"])

    def test_upload_duplicate_slot_returns_errors(self):
        csv_text = (
            "Time,Team A,Team B,Group,Court\n"
            "2026-06-01 10:00,AlphaCSV,BetaCSV,A,1\n"
            "2026-06-01 10:00,AlphaCSV,BetaCSV,A,1\n"
        )
        r = self._upload(csv_text)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["csv_errors"])

    def test_upload_empty_file_shows_error(self):
        r = self.client.post(self.url, {})
        self.assertEqual(r.status_code, 200)

    def test_confirm_expired_session_shows_error(self):
        r = self.client.post(self.url, {"confirm": "1"})
        self.assertEqual(r.status_code, 200)

    def test_multiple_rows_imported(self):
        team_c = _make_team("GammaCSV", group="B")
        team_d = _make_team("DeltaCSV", group="B")
        csv_text = (
            "Time,Team A,Team B,Group,Court,Stage\n"
            "2026-06-01 10:00,AlphaCSV,BetaCSV,A,1,GROUP\n"
            "2026-06-01 10:00,GammaCSV,DeltaCSV,B,2,GROUP\n"
        )
        self._upload(csv_text)
        r = self.client.post(self.url, {"confirm": "1"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Match.objects.count(), 2)

    def test_semicolon_delimiter_accepted(self):
        csv_text = (
            "Time;Team A;Team B;Group;Court;Stage\n"
            "2026-06-01 10:00;AlphaCSV;BetaCSV;A;1;GROUP\n"
        )
        r = self._upload(csv_text)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["preview"])


# ── 17.6 Gallery CRUD ───────────────────────────────────


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelGallery(TestCase):
    """Photo and video add/delete in the gallery."""

    def setUp(self):
        self.user = User.objects.create_user("st", "s@t.com", "pw", is_staff=True)
        self.client.login(username="st", password="pw")

    def test_add_photo(self):
        r = self.client.post(reverse("panel:gallery_add"), {
            "title": "Test Photo",
            "drive_url": "https://drive.google.com/file/d/abc123XYZ_90/view",
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(GalleryPhoto.objects.filter(drive_file_id="abc123XYZ_90").exists())

    def test_add_photo_bad_url(self):
        r = self.client.post(reverse("panel:gallery_add"), {
            "title": "Bad",
            "drive_url": "https://example.com/not-drive",
        })
        self.assertEqual(r.status_code, 200)  # re-renders form with error
        self.assertEqual(GalleryPhoto.objects.count(), 0)

    def test_delete_photo(self):
        photo = GalleryPhoto.objects.create(
            title="Del", drive_file_id="delid123", drive_url="https://d.com",
            thumbnail_url="https://d.com/t", order=1,
        )
        r = self.client.post(reverse("panel:gallery_delete", args=[photo.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(GalleryPhoto.objects.filter(pk=photo.pk).exists())

    def test_add_video(self):
        r = self.client.post(reverse("panel:video_add"), {
            "title": "Test Video",
            "drive_url": "https://drive.google.com/file/d/vidABC123_x/view",
            "description": "A video",
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(GalleryVideo.objects.filter(drive_file_id="vidABC123_x").exists())

    def test_delete_video(self):
        vid = GalleryVideo.objects.create(
            title="DelVid", drive_file_id="vdelid", drive_url="https://d.com",
            thumbnail_url="https://d.com/t", order=1,
        )
        r = self.client.post(reverse("panel:video_delete", args=[vid.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(GalleryVideo.objects.filter(pk=vid.pk).exists())

    def test_reorder_photos(self):
        p1 = GalleryPhoto.objects.create(
            drive_file_id="ro1", drive_url="https://d.com", order=0,
        )
        p2 = GalleryPhoto.objects.create(
            drive_file_id="ro2", drive_url="https://d.com", order=1,
        )
        r = self.client.post(
            reverse("panel:gallery_reorder"),
            data=f"[{p2.pk},{p1.pk}]",
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(p2.order, 0)
        self.assertEqual(p1.order, 1)


# ── 17.7 Dream Team CRUD / autofill / reset ─────────────


@override_settings(STORAGES=_STATIC_OVERRIDE)
class TestPanelDreamTeam(TestCase):
    """Dream Team admin: save, autofill, reset."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("st", "s@t.com", "pw", is_staff=True)
        cls.team_a = _make_team("DTA")
        cls.team_b = _make_team("DTB")
        cls.players_a = _make_players(cls.team_a, 6, start_jersey=1)
        cls.players_b = _make_players(cls.team_b, 6, start_jersey=11)
        cls.match = _make_match(cls.team_a, cls.team_b, number=1,
                                status=MATCH_FINISHED, score_a=2, score_b=1)
        # OH stats for team_a
        for p in cls.players_a:
            PlayerMatchStats.objects.create(
                match=cls.match, player=p, team=cls.team_a,
                position="OH", jersey_number=p.jersey_number,
                kills=10, aces=2, blocks=1, attack_attempts=20,
                serve_attempts=10, pass_attempts=10, perfect_passes=5,
            )
        # MB stats for team_b
        for p in cls.players_b:
            PlayerMatchStats.objects.create(
                match=cls.match, player=p, team=cls.team_b,
                position="MB", jersey_number=p.jersey_number,
                kills=3, aces=0, blocks=8, attack_attempts=8,
                serve_attempts=4, pass_attempts=6, perfect_passes=2,
            )

    def setUp(self):
        self.client.login(username="st", password="pw")

    def test_dreamteam_page_loads(self):
        r = self.client.get(reverse("panel:dreamteam"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "pnl-dt-court")

    def test_manual_save(self):
        p = self.players_a[0]
        r = self.client.post(reverse("panel:dreamteam"), {
            f"player_front-left": p.pk,
            f"metric_label_front-left": "10 kills",
            f"metric_value_front-left": "10",
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(DreamTeamEntry.objects.count(), 1)
        entry = DreamTeamEntry.objects.first()
        self.assertEqual(entry.slot, "front-left")
        self.assertEqual(entry.player, p)
        self.assertFalse(entry.is_auto)

    def test_autofill_creates_entries(self):
        r = self.client.post(reverse("panel:dreamteam_autofill"))
        self.assertEqual(r.status_code, 302)
        # Should create entries based on stats (OH×2 + MB×2 = 4 at minimum)
        self.assertGreaterEqual(DreamTeamEntry.objects.count(), 4)
        self.assertTrue(all(e.is_auto for e in DreamTeamEntry.objects.all()))

    def test_reset_clears_entries(self):
        DreamTeamEntry.objects.create(
            position="OH", slot="front-left",
            player=self.players_a[0], team=self.team_a,
            metric_label="test", metric_value=1,
        )
        r = self.client.post(reverse("panel:dreamteam_reset"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(DreamTeamEntry.objects.count(), 0)

    def test_autofill_then_reset(self):
        self.client.post(reverse("panel:dreamteam_autofill"))
        self.assertGreater(DreamTeamEntry.objects.count(), 0)
        self.client.post(reverse("panel:dreamteam_reset"))
        self.assertEqual(DreamTeamEntry.objects.count(), 0)

    def test_manual_save_replaces_previous(self):
        # Save once
        p1 = self.players_a[0]
        self.client.post(reverse("panel:dreamteam"), {
            "player_front-left": p1.pk,
            "metric_label_front-left": "10 kills",
            "metric_value_front-left": "10",
        })
        self.assertEqual(DreamTeamEntry.objects.count(), 1)
        # Save again with different player
        p2 = self.players_a[1]
        self.client.post(reverse("panel:dreamteam"), {
            "player_front-left": p2.pk,
            "metric_label_front-left": "15 kills",
            "metric_value_front-left": "15",
        })
        self.assertEqual(DreamTeamEntry.objects.count(), 1)
        self.assertEqual(DreamTeamEntry.objects.first().player, p2)


# ── Roster Update (public captain page) ─────────────────


@override_settings(STORAGES=_STATIC_OVERRIDE,
                   EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RosterUpdateTests(TestCase):
    """Tests for the public captain roster-update page."""

    def setUp(self):
        self.url = reverse("roster_update")
        self.team = _make_team("Roster Team")
        self.players = _make_players(self.team, count=3)

    def _send_code(self, team=None):
        """Step 1: select team → code generated & emailed."""
        t = team or self.team
        return self.client.post(self.url, {
            "action": "select_team",
            "team_id": t.pk,
        })

    def _auth(self, code):
        """Step 2: enter code from email."""
        return self.client.post(self.url, {
            "action": "auth",
            "code": code,
        })

    # ── Step 1: Select team ──

    def test_get_shows_team_selection(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Select Your Team")

    def test_select_team_sends_code_email(self):
        from django.core import mail
        resp = self._send_code()
        self.team.refresh_from_db()
        self.assertTrue(len(self.team.roster_code) == 6)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.team.roster_code, mail.outbox[0].body)
        # Shows code-entry step
        self.assertEqual(resp.context["code_sent_team"], self.team)

    # ── Step 2: Enter code ──

    def test_wrong_code_denied(self):
        self._send_code()
        resp = self._auth("000000")
        self.assertContains(resp, "Incorrect code")
        self.assertIsNone(resp.context["authenticated_team"])

    def test_correct_code_shows_roster(self):
        self._send_code()
        self.team.refresh_from_db()
        resp = self._auth(self.team.roster_code)
        self.assertEqual(resp.context["authenticated_team"], self.team)
        self.assertEqual(len(resp.context["players"]), 3)

    # ── Step 3: Save ──

    def test_save_updates_players(self):
        self._send_code()
        self.team.refresh_from_db()
        self._auth(self.team.roster_code)
        p = self.players[0]
        resp = self.client.post(self.url, {
            "action": "save",
            "team_id": self.team.pk,
            "player_id": [str(p.pk)],
            f"jersey_{p.pk}": "42",
            f"position_{p.pk}": "S",
        })
        p.refresh_from_db()
        self.assertEqual(p.jersey_number, "42")
        self.assertEqual(p.position, "S")
        self.assertContains(resp, "Roster updated successfully")

    # ── Logo upload ──

    def test_upload_logo(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self._send_code()
        self.team.refresh_from_db()
        self._auth(self.team.roster_code)
        logo = SimpleUploadedFile("logo.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
                                  content_type="image/png")
        resp = self.client.post(self.url, {"action": "upload_logo", "logo": logo})
        self.team.refresh_from_db()
        self.assertTrue(self.team.logo_path.endswith(".png"))
        self.assertContains(resp, "Logo uploaded successfully")

    def test_upload_logo_rejects_large_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self._send_code()
        self.team.refresh_from_db()
        self._auth(self.team.roster_code)
        big = SimpleUploadedFile("big.png", b"\x00" * (6 * 1024 * 1024),
                                 content_type="image/png")
        resp = self.client.post(self.url, {"action": "upload_logo", "logo": big})
        self.assertContains(resp, "File too large")
