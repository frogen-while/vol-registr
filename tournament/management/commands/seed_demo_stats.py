"""
Seed demo player/team stats, game sets, MVPs, and highlights.

Populates stats for the semi-final match (M17: Pocket Aces Black vs North Side Six)
from the mock data in _sports_demo_bundle, then recalculates standings and dream team.

Usage:
    python manage.py seed_demo_stats
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from tournament.constants import (
    MATCH_FINISHED,
    MVP_MATCH,
    MVP_TOURNAMENT,
    STAGE_GROUP,
)
from tournament.models import (
    GameSet,
    Match,
    MatchHighlight,
    MVPSelection,
    Player,
    PlayerMatchStats,
    Team,
    TeamMatchStats,
)
from tournament.services import recalculate_dream_team, recalculate_standings


# ── Per-match demo stat data ─────────────────────────────
# Each entry: (match_number, home_stats, away_stats, set_scores)
# home_stats / away_stats: list of (jersey, first, last, pos, stats_dict)

_PA = "Pocket Aces Black"
_LS = "Lodz Spikers"

DEMO_MATCH_STATS = [
    {
        "match_number": 17,  # SF 1-4: PA vs North Side Six
        "home": _PA,
        "away": "North Side Six",
        "sets": [(25, 21), (22, 25), (15, 11)],
        "home_players": [
            (8, "Daria", "Yasenovska", "OH", {"serve_attempts": 8, "aces": 2, "serve_errors": 1, "kills": 13, "attack_errors": 4, "pass_errors": 2, "blocks": 2, "assists": 0, "setting_errors": 0}),
            (11, "Ivan", "Bilovets", "OPP", {"serve_attempts": 7, "aces": 1, "serve_errors": 2, "kills": 10, "attack_errors": 4, "pass_errors": 0, "blocks": 3, "assists": 0, "setting_errors": 0}),
            (5, "Ihor", "Kornienko", "MB", {"serve_attempts": 6, "aces": 1, "serve_errors": 1, "kills": 6, "attack_errors": 2, "pass_errors": 0, "blocks": 4, "assists": 0, "setting_errors": 0}),
            (2, "Maksym", "Kotsiubailo", "S", {"serve_attempts": 7, "aces": 1, "serve_errors": 1, "kills": 1, "attack_errors": 0, "pass_errors": 0, "blocks": 1, "assists": 19, "setting_errors": 2}),
            (14, "Dima", "Vinohradow", "L", {"serve_attempts": 0, "aces": 0, "serve_errors": 0, "kills": 0, "attack_errors": 0, "pass_errors": 2, "blocks": 0, "assists": 0, "setting_errors": 0}),
            (7, "Marta", "Sydor", "OH", {"serve_attempts": 6, "aces": 1, "serve_errors": 2, "kills": 5, "attack_errors": 2, "pass_errors": 2, "blocks": 0, "assists": 0, "setting_errors": 0}),
        ],
        "away_players": [
            (3, "Maja", "Wozniak", "OH", {"serve_attempts": 8, "aces": 2, "serve_errors": 2, "kills": 11, "attack_errors": 6, "pass_errors": 3, "blocks": 1, "assists": 0, "setting_errors": 0}),
            (10, "Olena", "Martynenko", "MB", {"serve_attempts": 7, "aces": 1, "serve_errors": 2, "kills": 7, "attack_errors": 2, "pass_errors": 0, "blocks": 3, "assists": 0, "setting_errors": 0}),
            (9, "Kasia", "Grudzien", "OPP", {"serve_attempts": 5, "aces": 0, "serve_errors": 1, "kills": 9, "attack_errors": 5, "pass_errors": 0, "blocks": 1, "assists": 0, "setting_errors": 0}),
            (1, "Lena", "Polak", "S", {"serve_attempts": 6, "aces": 0, "serve_errors": 1, "kills": 2, "attack_errors": 1, "pass_errors": 0, "blocks": 0, "assists": 17, "setting_errors": 2}),
            (15, "Julia", "Rek", "L", {"serve_attempts": 0, "aces": 0, "serve_errors": 0, "kills": 0, "attack_errors": 0, "pass_errors": 4, "blocks": 0, "assists": 0, "setting_errors": 0}),
            (16, "Nina", "Sikora", "OH", {"serve_attempts": 7, "aces": 1, "serve_errors": 2, "kills": 6, "attack_errors": 4, "pass_errors": 3, "blocks": 2, "assists": 0, "setting_errors": 0}),
        ],
    },
]

HIGHLIGHTS = [
    {"title": "Semi final recap", "description": "Pocket Aces vs North Side Six in one sharp cut.", "order": 1},
    {"title": "Top 10 tournament plays", "description": "Best swings, blocks and serving runs.", "order": 2},
    {"title": "Dream Team reveal", "description": "Court graphic + seven best positions.", "order": 3},
]


class Command(BaseCommand):
    help = "Seed demo stats, game sets, MVPs, and highlights from mock data."

    def handle(self, *args, **options):
        stats_created = 0

        for entry in DEMO_MATCH_STATS:
            match = self._get_match(entry["match_number"])
            if match is None:
                continue

            # Clean previous
            PlayerMatchStats.objects.filter(match=match).delete()
            TeamMatchStats.objects.filter(match=match).delete()
            GameSet.objects.filter(match=match).delete()

            home_team = self._get_team(entry["home"])
            away_team = self._get_team(entry["away"])
            if not home_team or not away_team:
                continue

            # Game sets
            for i, (sa, sb) in enumerate(entry["sets"], start=1):
                GameSet.objects.create(match=match, set_number=i, score_a=sa, score_b=sb)

            # Player stats
            for jersey, first, last, pos, stats in entry["home_players"]:
                player = self._resolve_player(home_team, jersey, first, last)
                if player:
                    PlayerMatchStats.objects.create(
                        match=match, player=player, team=home_team,
                        position=pos, jersey_number=jersey, **stats,
                    )
                    stats_created += 1

            for jersey, first, last, pos, stats in entry["away_players"]:
                player = self._resolve_player(away_team, jersey, first, last)
                if player:
                    PlayerMatchStats.objects.create(
                        match=match, player=player, team=away_team,
                        position=pos, jersey_number=jersey, **stats,
                    )
                    stats_created += 1

            # Team totals
            self._aggregate_team(match, home_team)
            self._aggregate_team(match, away_team)

            # Update match score
            home_sets = sum(1 for sa, sb in entry["sets"] if sa > sb)
            away_sets = sum(1 for sa, sb in entry["sets"] if sb > sa)
            match.score_a = home_sets
            match.score_b = away_sets
            match.status = MATCH_FINISHED
            match.stats_imported = True
            match.save(update_fields=["score_a", "score_b", "status", "stats_imported"])

            # Match MVP
            mvp = (
                PlayerMatchStats.objects.filter(match=match)
                .order_by("-kills", "-blocks", "-aces")
                .first()
            )
            if mvp:
                MVPSelection.objects.update_or_create(
                    mvp_type=MVP_MATCH, match=match,
                    defaults={
                        "player": mvp.player,
                        "team": mvp.team,
                        "reason": f"{mvp.kills} kills, {mvp.blocks} blocks",
                    },
                )

        # Tournament MVP — top scorer overall
        from django.db.models import Sum
        top = (
            PlayerMatchStats.objects
            .values("player_id", "team_id")
            .annotate(total_kills=Sum("kills"))
            .order_by("-total_kills")
            .first()
        )
        if top:
            MVPSelection.objects.update_or_create(
                mvp_type=MVP_TOURNAMENT, match=None,
                defaults={
                    "player_id": top["player_id"],
                    "team_id": top["team_id"],
                    "reason": f"{top['total_kills']} total kills",
                },
            )

        # Highlights
        MatchHighlight.objects.all().delete()
        sf_match = Match.objects.filter(match_number=17).first()
        for h in HIGHLIGHTS:
            MatchHighlight.objects.create(
                match=sf_match,
                title=h["title"],
                description=h["description"],
                order=h["order"],
            )

        # Recalculate
        recalculate_standings()
        recalculate_dream_team()

        self.stdout.write(self.style.SUCCESS(
            f"Demo stats seeded: {stats_created} player stats, "
            f"{MatchHighlight.objects.count()} highlights"
        ))

    def _get_match(self, match_number):
        try:
            return Match.objects.get(match_number=match_number)
        except Match.DoesNotExist:
            self.stderr.write(self.style.WARNING(
                f"  Match M{match_number} not found — run seed_schedule first"
            ))
            return None

    def _get_team(self, name):
        try:
            return Team.objects.get(name=name)
        except Team.DoesNotExist:
            self.stderr.write(self.style.WARNING(f"  Team '{name}' not found"))
            return None

    def _resolve_player(self, team, jersey, first_name, last_name):
        """Find or create a player by jersey number on the team."""
        player = team.players.filter(jersey_number=jersey).first()
        if player:
            return player
        # Try by name
        player = team.players.filter(first_name=first_name, last_name=last_name).first()
        if player:
            return player
        # Auto-create for demo purposes
        player = Player.objects.create(
            team=team,
            first_name=first_name,
            last_name=last_name,
            jersey_number=jersey,
        )
        self.stdout.write(f"  Auto-created player: {player} for {team.name}")
        return player

    def _aggregate_team(self, match, team):
        from django.db.models import Sum
        agg_fields = [
            "serve_attempts", "aces", "serve_errors",
            "attack_attempts", "kills", "attack_errors",
            "pass_attempts", "perfect_passes", "pass_errors",
            "blocks",
        ]
        agg = PlayerMatchStats.objects.filter(
            match=match, team=team,
        ).aggregate(**{f: Sum(f) for f in agg_fields})
        TeamMatchStats.objects.update_or_create(
            match=match, team=team,
            defaults={f: agg[f] or 0 for f in agg_fields},
        )
