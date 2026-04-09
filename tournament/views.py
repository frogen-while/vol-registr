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

from .constants import MAX_TOURNAMENT_SLOTS, PAYMENT_ACCOUNTS
from .forms import TeamRegistrationForm
from .models import GalleryPhoto, GalleryVideo, Match, Team
from .services import get_available_slots, register_team
from .sports_data import (
    get_category_leaders,
    get_dream_team,
    get_highlights,
    get_match_detail,
    get_mvp,
    get_player_detail,
    get_schedule_slots,
    get_standings,
    get_team_detail,
)

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


def tournament_hub(request):
    """Tournament hub page — standings, schedule, highlights."""
    from django.utils import timezone
    import datetime

    unlock_at = datetime.datetime(2026, 4, 11, 9, 0, 0, tzinfo=datetime.timezone.utc)
    if timezone.now() < unlock_at:
        return render(request, "tournament/match_coming_soon.html", {
            "unlock_iso": unlock_at.isoformat(),
            "page_title": "Tournament Hub — Coming Soon",
        })

    context = {
        "active": "hub",
        "standings": get_standings("groups"),
        "overall_standings": get_standings("overall"),
        "schedule_slots": get_schedule_slots(),
        "highlights": get_highlights(),
        "page_title": "Tournament Hub — Pocket Aces Volleyball",
        "page_description": "Live standings, schedule, and highlights from the Pocket Aces Spring Volleyball Tournament.",
    }
    return render(request, "tournament/tournament_preview.html", context)


def tournament_teams(request):
    """Teams list page grouped by group."""
    standings = get_standings("groups")
    overall = get_standings("overall")
    dream_team_entries = get_dream_team()
    if dream_team_entries:
        dream_team_spotlight = dream_team_entries[:3]
    else:
        dream_team_spotlight = [
            {
                "position": leader["label"],
                "name": leader["player_name"],
                "team": leader["team"],
                "team_logo": leader.get("team_logo", ""),
                "metric": leader["value"],
                "player_id": leader.get("player_id"),
                "image": leader["image"],
            }
            for leader in get_category_leaders()[:3]
        ]

    # Fallback: show registered teams when no standings computed yet
    teams = []
    if not standings and not overall:
        teams = list(
            Team.objects.all()
            .order_by("group_name", "name")
            .values("id", "name", "group_name", "league_level", "logo_path")
        )

    context = {
        "active": "teams",
        "standings": standings,
        "overall_standings": overall,
        "teams": teams,
        "dream_team_spotlight": dream_team_spotlight,
        "dream_team_total": len(dream_team_entries) or len(dream_team_spotlight),
        "page_title": "All Teams — Pocket Aces Tournament",
        "page_description": "Browse all teams competing in the Pocket Aces Spring Volleyball Tournament.",
    }
    return render(request, "tournament/teams_preview.html", context)


def tournament_dream_team(request):
    """Visual Dream Team court page."""
    from .constants import MVP_TOURNAMENT
    context = {
        "active": "dream_team",
        "dream_team": get_dream_team(),
        "category_leaders": get_category_leaders(),
        "mvp": get_mvp(MVP_TOURNAMENT),
        "page_title": "Dream Team — Pocket Aces Tournament",
        "page_description": "The best players of the tournament selected for the Pocket Aces Dream Team.",
    }
    return render(request, "tournament/dream_team_preview.html", context)


def tournament_match(request, match_id):
    """Match detail page by ID."""
    detail = get_match_detail(match_id)
    if detail is None:
        from django.http import Http404
        raise Http404("Match not found")
    m = detail["match"]
    detail["page_title"] = f"{m['home']['name']} vs {m['away']['name']} — Pocket Aces"
    detail["page_description"] = f"{m['stage']} match: {m['home']['name']} vs {m['away']['name']}. Score, stats, and highlights."
    return render(request, "tournament/match_preview.html", detail)


def tournament_team(request, team_id):
    """Team stats page by ID — roster, match history, stats."""
    detail = get_team_detail(team_id)
    if detail is None:
        from django.http import Http404
        raise Http404("Team not found")
    detail["page_title"] = f"{detail['team_profile']['name']} — Pocket Aces Tournament"
    detail["page_description"] = f"Roster, match history and stats for {detail['team_profile']['name']}."
    return render(request, "tournament/team_preview.html", detail)


def tournament_player(request, player_id):
    """Player detail page — first-class public destination."""
    detail = get_player_detail(player_id)
    if detail is None:
        from django.http import Http404
        raise Http404("Player not found")
    ctx = detail
    ctx["page_title"] = f"{detail['player_profile']['name']} — Pocket Aces Tournament"
    ctx["page_description"] = (
        f"Stats, match log, and awards for {detail['player_profile']['name']} "
        f"({detail['player_profile']['position']}) of {detail['player_profile']['team']}."
    )
    return render(request, "tournament/player_preview.html", ctx)


def tournament_gallery(request):
    """Public gallery page — photos grid + video cards."""
    photos = GalleryPhoto.objects.order_by("order", "-uploaded_at")
    videos = GalleryVideo.objects.order_by("order", "-uploaded_at")
    return render(request, "tournament/gallery.html", {
        "active": "gallery",
        "photos": photos,
        "videos": videos,
        "page_title": "Gallery — Pocket Aces Volleyball",
        "page_description": "Photos and video highlights from the Pocket Aces Spring Volleyball Tournament.",
    })

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
                subject = "Rejestracja zakoÅ„czona — Instrukcje pÅ‚atnoÅ›ci"
                message = (
                    f"DziÄ™kujemy za rejestracjÄ™ druÅ¼yny {team.name} na turniej Pocket Aces!\n\n"
                    "Aby dokoÅ„czyÄ‡ rejestracjÄ™, prosimy o przelew opÅ‚aty startowej na poniÅ¼sze konto:\n"
                    f"BLIK: {blik}\n"
                    f"TytuÅ‚: {team.name}\n\n"
                    "W razie pytaÅ„ odpowiedz na tego maila.\n\n"
                    "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "Do zobaczenia na boisku! ðŸ\n\n"
                    "Z powaÅ¼aniem\n"
                    "ZespÃ³Å‚ Pocket Aces Sports Club\n"
                )
            else:
                subject = "Registration Successful — Payment Instructions"
                message = (
                    f"Thank you for registering {team.name} for the Pocket Aces tournament!\n\n"
                    "To complete your registration, please transfer the entry fee to the following account:\n"
                    f"BLIK: {blik}\n"
                    f"Title: Pocket Aces Registration — {team.name}\n\n"
                    "If you have any questions, reply to this email.\n\n"
                    "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "See you on the court! ðŸ\n\n"
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


# â”€â”€ Captain Roster Update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@ensure_csrf_cookie
def roster_update_view(request):
    """
    Public page where captains update jersey numbers and positions.

    Flow: select team â†’ code sent to captain email â†’ enter code â†’ edit roster.
    """
    import random
    from .constants import POSITION_CHOICES, ROSTER_CODE_LENGTH

    teams = Team.objects.order_by("name")
    error = ""
    success = ""
    authenticated_team = None
    players = None
    # Which team was selected (to show code-entry step)
    code_sent_team = None

    if request.method == "POST":
        action = request.POST.get("action", "")
        team_id = request.POST.get("team_id", "")

        if action == "select_team":
            # â”€â”€ Step 1: Generate code and email it to captain â”€â”€
            if not team_id:
                error = "Please select a team."
            else:
                try:
                    team = Team.objects.get(pk=int(team_id))
                except (Team.DoesNotExist, ValueError):
                    error = "Team not found."
                    team = None

                if team:
                    code = "".join(
                        random.choices("0123456789", k=ROSTER_CODE_LENGTH)
                    )
                    team.roster_code = code
                    team.save(update_fields=["roster_code"])
                    try:
                        send_mail(
                            subject="Pocket Aces — Roster Access Code",
                            message=(
                                f"Hi {team.cap_name},\n\n"
                                f"Your roster access code for team "
                                f'"{team.name}" is: {code}\n\n'
                                "Enter this code on the Roster Update page "
                                "to edit jersey numbers and positions.\n\n"
                                "— Pocket Aces Invitational"
                            ),
                            from_email=None,  # uses DEFAULT_FROM_EMAIL
                            recipient_list=[team.cap_email],
                        )
                    except Exception:
                        logger.exception("Failed to send roster code email")
                        error = "Failed to send email. Please try again or contact the organizer."
                    else:
                        # Mask email: s****@gmail.com
                        email = team.cap_email
                        at = email.index("@")
                        masked = email[0] + "****" + email[at:]
                        success = f"Code sent to {masked}"
                        code_sent_team = team
                        request.session["_roster_team_id"] = team.pk

        elif action == "auth":
            # â”€â”€ Step 2: Verify code entered by captain â”€â”€
            code = request.POST.get("code", "").strip()
            sess_team_id = request.session.get("_roster_team_id")
            if not sess_team_id:
                error = "Session expired. Please start over."
            elif not code:
                error = "Please enter the access code."
            else:
                try:
                    team = Team.objects.get(pk=int(sess_team_id))
                except (Team.DoesNotExist, ValueError):
                    error = "Team not found."
                    team = None

                if team:
                    if not team.roster_code:
                        error = "No code has been generated. Please start over."
                    elif team.roster_code != code:
                        error = "Incorrect code. Please check your email and try again."
                        code_sent_team = team  # stay on code-entry step
                    else:
                        authenticated_team = team
                        players = team.players.all().order_by("pk")
                        request.session["_roster_code"] = code

        elif action == "save":
            # â”€â”€ Step 3: Save roster changes â”€â”€
            sess_team_id = request.session.get("_roster_team_id")
            sess_code = request.session.get("_roster_code")
            if not sess_team_id or not sess_code:
                error = "Session expired. Please authenticate again."
            else:
                try:
                    team = Team.objects.get(pk=sess_team_id)
                except Team.DoesNotExist:
                    error = "Team not found."
                    team = None

                if team and team.roster_code != sess_code:
                    error = "Session invalid. Please authenticate again."
                    team = None

                if team:
                    player_ids = request.POST.getlist("player_id")
                    for pid in player_ids:
                        try:
                            player = team.players.get(pk=int(pid))
                        except (team.players.model.DoesNotExist, ValueError):
                            continue
                        jersey_raw = request.POST.get(f"jersey_{pid}", "").strip()
                        position_raw = request.POST.get(f"position_{pid}", "").strip()
                        jersey = ""
                        if jersey_raw:
                            if jersey_raw.isdigit() and len(jersey_raw) <= 3:
                                jersey = jersey_raw
                            else:
                                jersey = player.jersey_number
                        player.jersey_number = jersey
                        valid_positions = {c[0] for c in POSITION_CHOICES}
                        player.position = position_raw if position_raw in valid_positions else ""
                        player.save(update_fields=["jersey_number", "position"])

                    authenticated_team = team
                    players = team.players.all().order_by("pk")
                    success = "Roster updated successfully!"

        elif action == "upload_logo":
            # â”€â”€ Upload team logo â”€â”€
            import os

            sess_team_id = request.session.get("_roster_team_id")
            sess_code = request.session.get("_roster_code")
            if not sess_team_id or not sess_code:
                error = "Session expired. Please authenticate again."
            else:
                try:
                    team = Team.objects.get(pk=sess_team_id)
                except Team.DoesNotExist:
                    error = "Team not found."
                    team = None

                if team and team.roster_code != sess_code:
                    error = "Session invalid. Please authenticate again."
                    team = None

                if team:
                    logo_file = request.FILES.get("logo")
                    if not logo_file:
                        error = "Please select an image file."
                    elif logo_file.size > 5 * 1024 * 1024:
                        error = "File too large. Maximum size is 5 MB."
                    elif logo_file.content_type not in (
                        "image/png", "image/jpeg", "image/webp",
                    ):
                        error = "Only PNG, JPEG, or WebP images are allowed."
                    else:
                        ext = os.path.splitext(logo_file.name)[1].lower()
                        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                            ext = ".png"
                        filename = f"team_{team.pk}{ext}"
                        upload_dir = os.path.join(
                            settings.MEDIA_ROOT, "team_logos"
                        )
                        os.makedirs(upload_dir, exist_ok=True)
                        filepath = os.path.join(upload_dir, filename)
                        with open(filepath, "wb") as f:
                            for chunk in logo_file.chunks():
                                f.write(chunk)
                        team.logo_path = f"team_logos/{filename}"
                        team.save(update_fields=["logo_path"])
                        success = "Logo uploaded successfully!"

                    authenticated_team = team
                    players = team.players.all().order_by("pk")

    return render(request, "tournament/roster_update.html", {
        "teams": teams,
        "error": error,
        "success": success,
        "authenticated_team": authenticated_team,
        "code_sent_team": code_sent_team,
        "players": players,
        "position_choices": POSITION_CHOICES,
        "MEDIA_URL": settings.MEDIA_URL,
    })
