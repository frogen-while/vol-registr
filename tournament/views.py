def privacy_policy_en(request):
    """Privacy Policy page (EN)."""
    return render(request, "tournament/pivate_policy_en.html")
"""Thin view layer — delegates logic to forms and services."""

import json
import logging
from django.conf import settings

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail

from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


def faq(request):
    """FAQ page."""
    return render(request, "tournament/faq.html")

from .constants import MAX_TOURNAMENT_SLOTS, PAYMENT_ACCOUNTS
from .forms import TeamRegistrationForm
from .models import Team
from .services import get_available_slots, register_team

logger = logging.getLogger(__name__)


def index(request):
    """Landing page with live slot counter."""
    available = get_available_slots()
    teams = Team.objects.all().order_by('created_at')
    context = {
        "available_slots": available,
        "registered_teams": MAX_TOURNAMENT_SLOTS - available,
        "max_slots": MAX_TOURNAMENT_SLOTS,
        "teams": teams,
    }
    return render(request, "tournament/index.html", context)

def team_detail(request, team_id):
    """Team detail page showing roster and captain info."""
    team = get_object_or_404(Team, id=team_id)
    return render(request, "tournament/team_detail.html", {"team": team})

@ensure_csrf_cookie
def register(request):
    """Registration form page (renders the empty form + CSRF cookie)."""
    return render(request, "tournament/register.html")

from django.contrib.admin.views.decorators import staff_member_required
from .models import Match, GameSet, MatchEvent, Player

@staff_member_required
def scorer_dashboard(request, match_id):
    """Scorer Dashboard view. Requires staff permissions."""
    match = get_object_or_404(Match, id=match_id)
    # Get the active game set (if none, get the latest or create one)
    active_set = match.sets.filter(is_completed=False).first()
    if not active_set:
        last_set = match.sets.order_by('-set_number').first()
        next_set_num = 1 if not last_set else last_set.set_number + 1
        active_set = GameSet.objects.create(match=match, set_number=next_set_num)
        
    context = {
        'match': match,
        'active_set': active_set,
        'team_a': match.team_a,
        'team_b': match.team_b,
    }
    return render(request, 'tournament/scorer_dashboard.html', context)

@staff_member_required
@require_POST
def record_event(request, match_id):
    """API endpoint to record an event from the scorer dashboard."""
    try:
        data = json.loads(request.body)
        game_set_id = data.get('set_id')
        team_id = data.get('team_id')
        player_id = data.get('player_id')
        category = data.get('category')
        result = data.get('result')
        affected_player_id = data.get('affected_player_id')
        
        game_set = get_object_or_404(GameSet, id=game_set_id, match_id=match_id)
        team = get_object_or_404(Team, id=team_id)
        player = get_object_or_404(Player, id=player_id)
        affected_player = Player.objects.filter(id=affected_player_id).first() if affected_player_id else None

        # Determine points:
        point_awarded_to = None
        if result in ['K', 'SA', 'BS', 'BA']: # point for attacking/serving/blocking team
            point_awarded_to = team
        elif result in ['E', 'SE', 'RE', 'BE']: # point for defending team
            point_awarded_to = game_set.match.team_a if team == game_set.match.team_b else game_set.match.team_b

        if point_awarded_to:
            if point_awarded_to == game_set.match.team_a:
                game_set.score_a += 1
            else:
                game_set.score_b += 1
            game_set.save()

        # Create the event
        event = MatchEvent.objects.create(
            match_id=match_id,
            game_set=game_set,
            team=team,
            player=player,
            category=category,
            result=result,
            affected_player=affected_player,
            score_a_at_time=game_set.score_a,
            score_b_at_time=game_set.score_b
        )

        return JsonResponse({
            'status': 'success',
            'new_score_a': game_set.score_a,
            'new_score_b': game_set.score_b,
            'event_id': event.id
        })
    except Exception as e:
        logger.exception("Error recording match event")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@staff_member_required
@require_POST
def undo_event(request, match_id):
    """Reverts the last match event and restores score."""
    try:
        data = json.loads(request.body)
        event_id = data.get('event_id')
        
        event = get_object_or_404(MatchEvent, id=event_id, match_id=match_id)
        game_set = event.game_set
        
        # We need to figure out who got the point in order to decrement it.
        # Check if there is a previous event in the set:
        previous_events = MatchEvent.objects.filter(
            game_set=game_set, 
            timestamp__lt=event.timestamp
        ).order_by('-timestamp')
        
        if previous_events.exists():
            prev = previous_events.first()
            game_set.score_a = prev.score_a_at_time
            game_set.score_b = prev.score_b_at_time
        else:
            game_set.score_a = 0
            game_set.score_b = 0
            
        game_set.save()
        event.delete()

        return JsonResponse({
            'status': 'success',
            'new_score_a': game_set.score_a,
            'new_score_b': game_set.score_b,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)




@require_POST
def api_register_team(request):
    """
    JSON endpoint: validate and create a team.

    Returns
    -------
    JsonResponse  {success: bool, team_id?: int, error?: str}
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON payload."}, status=400
        )

    form = TeamRegistrationForm(data)
    if not form.is_valid():
        # Return the first validation error
        first_error = next(iter(form.errors.values()))[0]
        return JsonResponse({"success": False, "error": first_error}, status=400)


    try:
        players_data = data.get("players", [])
        team = register_team(form.cleaned_data, players_data=players_data)

        # Send payment instructions email
        user_email = form.cleaned_data.get('email')
        lang = data.get('lang', 'en')
        if lang not in ('en', 'pl'):
            lang = 'en'

        if user_email:
            # Assign BLIK by capacity: 6 / 3 / 3
            blik = PAYMENT_ACCOUNTS[0]["blik"]  # fallback
            for account in PAYMENT_ACCOUNTS:
                used = Team.objects.filter(blik_number=account["blik"]).count()
                if used < account["capacity"]:
                    blik = account["blik"]
                    break
            team.blik_number = blik
            team.save(update_fields=["blik_number"])

            if lang == 'pl':
                subject = "Rejestracja zakończona – Instrukcje płatności"
                message = (
                    f"Dziękujemy za rejestrację drużyny {team.name} na turniej Pocket Aces!\n\n"
                    "Aby dokończyć rejestrację, prosimy o przelew opłaty startowej na poniższe konto:\n"
                    f"BLIK: {blik}\n"
                    f"Tytuł: {team.name}\n\n"
                    "W razie pytań odpowiedz na tego maila.\n\n"
                    "─────────────────────────────\n"
                    "Do zobaczenia na boisku! 🏐\n\n"
                    "Z poważaniem\n"
                    "Zespół Pocket Aces Sports Club\n"
                )
            else:
                subject = "Registration Successful – Payment Instructions"
                message = (
                    f"Thank you for registering {team.name} for the Pocket Aces tournament!\n\n"
                    "To complete your registration, please transfer the entry fee to the following account:\n"
                    f"BLIK: {blik}\n"
                    f"Title: Pocket Aces Registration – {team.name}\n\n"
                    "If you have any questions, reply to this email.\n\n"
                    "─────────────────────────────\n"
                    "See you on the court! 🏐\n\n"
                    "Best regards,\n"
                    "Pocket Aces Sports Club Team\n"
                )

            send_mail(
                subject=subject,
                message=message,
                from_email=None,  # Uses DEFAULT_FROM_EMAIL
                recipient_list=[user_email],
                fail_silently=False,
            )

        return JsonResponse({"success": True, "team_id": team.id})

    except ValueError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)

    except Exception:
        logger.exception("Unexpected error during team registration")
        return JsonResponse(
            {"success": False, "error": "Internal server error."}, status=500
        )

@require_POST
def api_ask_question(request):
    """
    JSON endpoint: send a question to the organizers.
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        question = data.get('question')
        
        if not email or not question:
             return JsonResponse({'success': False, 'error': 'Email and question are required.'}, status=400)

        # Send email to admin (self)
        send_mail(
            subject=f'New Question from {email}',
            message=f'Sender: {email}\n\nQuestion:\n{question}',
            from_email=None, 
            recipient_list=[settings.DEFAULT_FROM_EMAIL], 
            fail_silently=False,
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f'Error sending question: {e}')
        return JsonResponse({'success': False, 'error': 'Failed to send question.'}, status=500)
