from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # ── Tournament section ──────────────────────────────
    path('tournament/', views.tournament_hub, name='tournament_hub'),
    path('tournament/teams/', views.tournament_teams, name='tournament_teams'),
    path('tournament/dream-team/', views.tournament_dream_team, name='tournament_dream_team'),
    path('tournament/match/<int:match_id>/', views.tournament_match, name='tournament_match'),
    path('tournament/team/<int:team_id>/', views.tournament_team, name='tournament_team'),
    path('tournament/player/<int:player_id>/', views.tournament_player, name='tournament_player'),
    path('tournament/gallery/', views.tournament_gallery, name='tournament_gallery'),
    # ── Other pages ─────────────────────────────────────
    path('register/', views.register, name='register'),
    path('faq/', views.faq, name='faq'),
    path('api/register/', views.api_register_team, name='api_register'),
    path('api/ask/', views.api_ask_question, name='api_ask_question'),
    path('є', views.roster_update_view, name='roster_update'),
    path('privacy-policy/', views.privacy_policy_en, name='privacy_policy_en'),
]
