def privacy_policy_en(request):
    """Privacy Policy page (EN)."""
    return render(request, "tournament/pivate_policy_en.html")
"""Thin view layer — delegates logic to forms and services."""

import json
import logging
from django.conf import settings

from django.http import JsonResponse
from django.shortcuts import render
from django.core.mail import send_mail

from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


def faq(request):
    """FAQ page."""
    return render(request, "tournament/faq.html")

from .constants import MAX_TOURNAMENT_SLOTS
from .forms import TeamRegistrationForm
from .services import get_available_slots, register_team

logger = logging.getLogger(__name__)


def index(request):
    """Landing page with live slot counter."""
    available = get_available_slots()
    context = {
        "available_slots": available,
        "registered_teams": MAX_TOURNAMENT_SLOTS - available,
        "max_slots": MAX_TOURNAMENT_SLOTS,
    }
    return render(request, "tournament/index.html", context)


@ensure_csrf_cookie
def register(request):
    """Registration form page (renders the empty form + CSRF cookie)."""
    return render(request, "tournament/register.html")


@ensure_csrf_cookie
def register(request):
    """Registration form page (renders the empty form + CSRF cookie)."""
    return render(request, "tournament/register.html")




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
        if user_email:
            send_mail(
                subject="Registration Successful – Payment Instructions",
                message=(
                    "Thank you for registering for the tournament!\n\n"
                    "To complete your registration, please transfer the entry fee to the following account:\n"
                    "IBAN: [YOUR IBAN HERE]\n"
                    "Title: Pocket Aces Registration – [Your Team Name]\n\n"
                    "If you have any questions, reply to this email."
                ),
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
