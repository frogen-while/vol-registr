"""Thin view layer — delegates logic to forms and services."""

import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .constants import MAX_TOURNAMENT_SLOTS
from .forms import TeamRegistrationForm
from .services import get_available_slots, register_team

logger = logging.getLogger(__name__)


def index(request):
    """Landing page with live slot counter."""
    context = {
        "available_slots": get_available_slots(),
        "max_slots": MAX_TOURNAMENT_SLOTS,
    }
    return render(request, "tournament/index.html", context)


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
        team = register_team(form.cleaned_data)
        return JsonResponse({"success": True, "team_id": team.id})

    except ValueError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)

    except Exception:
        logger.exception("Unexpected error during team registration")
        return JsonResponse(
            {"success": False, "error": "Internal server error."}, status=500
        )
