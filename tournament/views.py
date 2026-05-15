def privacy_policy_en(request):
    """Privacy Policy page (EN)."""
    return render(request, "tournament/pivate_policy_en.html")
"""Thin view layer — delegates logic to forms and services."""

import json
import logging
from pathlib import Path
import re
from types import SimpleNamespace
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core import signing
from django.db import models as db_models
from django.db import transaction

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static as static_url
from django.core.mail import send_mail
from django.urls import reverse

from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST


def faq(request):
    """FAQ page."""
    return render(request, "tournament/faq.html")

from .constants import MAX_TOURNAMENT_SLOTS, PAYMENT_ACCOUNTS
from .forms import TeamRegistrationForm
from .logo_utils import save_team_logo
from .models import GalleryPhoto, GalleryVideo, Match, Team, TeamFanVote
from .services import get_available_slots, register_team

logger = logging.getLogger(__name__)

SOUNDCLOUD_CLIENT_ID: str | None = None
PREV_TOUR_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PREV_TOUR_VIDEO_EXTENSIONS = {".mov", ".mp4", ".m4v"}

ROSTER_ACCESS_SALT = "tournament.roster-access"
ROSTER_ACCESS_MAX_AGE = 60 * 60 * 24 * 3
ROSTER_MIN_PLAYERS = 6

ROSTER_MESSAGE_DEFAULTS = {
    "rp.msg_link_invalid": "This access link is invalid or has expired.",
    "rp.msg_min_players": "Keep at least 6 players on the roster.",
    "rp.msg_profile_saved": "Team profile updated successfully!",
    "rp.msg_profile_team": "Team name is required.",
    "rp.msg_profile_captain": "Captain name is required.",
    "rp.msg_profile_email": "Captain email is required.",
    "rp.msg_profile_phone": "Captain phone is required.",
    "rp.msg_profile_player_name": "Each player needs both a first and last name.",
    "rp.msg_profile_team_conflict": "Another team already uses this name.",
    "rp.msg_profile_email_conflict": "Another team already uses this captain email.",
    "rp.msg_profile_phone_conflict": "Another team already uses this captain phone number.",
}


def _parse_registration_payload(request):
    content_type = request.content_type or ""
    if content_type.startswith("application/json"):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload.") from exc

        players_data = data.get("players", [])
        if not isinstance(players_data, list):
            raise ValueError("Invalid players payload.")
        return data, players_data, None

    players_raw = request.POST.get("players", "[]")
    try:
        players_data = json.loads(players_raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid players payload.") from exc

    if not isinstance(players_data, list):
        raise ValueError("Invalid players payload.")

    return request.POST.copy(), players_data, request.FILES.get("logo")


def _get_soundcloud_client_id() -> str:
    """Resolve a public SoundCloud client id from the web hydration payload and cache it."""
    global SOUNDCLOUD_CLIENT_ID
    if SOUNDCLOUD_CLIENT_ID:
        return SOUNDCLOUD_CLIENT_ID

    user_agent = "Mozilla/5.0"
    html = urlopen(
        Request("https://soundcloud.com/search/sounds?q=music", headers={"User-Agent": user_agent}),
        timeout=15,
    ).read().decode("utf-8", "ignore")

    def extract_client_id(source: str) -> str | None:
        hydration_match = re.search(r"__sc_hydration\s*=\s*(\[.*?\]);", source, re.S)
        if hydration_match:
            hydration_payload = json.loads(hydration_match.group(1))
            for item in hydration_payload:
                if item.get("hydratable") == "apiClient":
                    client_id = item.get("data", {}).get("id")
                    if client_id:
                        return client_id

        for pattern in (
            r'client_id["\']?\s*[:=]\s*["\']([A-Za-z0-9]{16,})["\']',
            r'clientId["\']?\s*[:=]\s*["\']([A-Za-z0-9]{16,})["\']',
        ):
            match = re.search(pattern, source)
            if match:
                return match.group(1)
        return None

    client_id = extract_client_id(html)
    if client_id:
        SOUNDCLOUD_CLIENT_ID = client_id
        return client_id

    asset_urls = list(dict.fromkeys(re.findall(r"https://a-v2\.sndcdn\.com/assets/[^\"']+\.js", html)))
    for asset_url in asset_urls[:8]:
        try:
            asset_source = urlopen(Request(asset_url, headers={"User-Agent": user_agent}), timeout=15).read().decode("utf-8", "ignore")
        except Exception:
            continue

        client_id = extract_client_id(asset_source)
        if client_id:
            SOUNDCLOUD_CLIENT_ID = client_id
            return client_id

    raise RuntimeError("SoundCloud client id not found")


def _build_prev_tour_static_media(existing_photo_ids: set[str], existing_video_ids: set[str]) -> tuple[list[SimpleNamespace], list[SimpleNamespace]]:
    """Expose bundled previous tournament assets even when the gallery tables are empty."""
    prev_tour_dir = Path(settings.BASE_DIR) / "static" / "assets" / "prev-tour"
    if not prev_tour_dir.exists():
        return [], []

    fallback_photos: list[SimpleNamespace] = []
    fallback_videos: list[SimpleNamespace] = []

    for asset_path in sorted(prev_tour_dir.iterdir(), key=lambda path: path.name.lower()):
        if not asset_path.is_file():
            continue

        extension = asset_path.suffix.lower()
        drive_file_id = f"local_prev_{asset_path.name}"
        drive_url = static_url(f"assets/prev-tour/{asset_path.name}")

        if extension in PREV_TOUR_IMAGE_EXTENSIONS and drive_file_id not in existing_photo_ids:
            fallback_photos.append(SimpleNamespace(
                drive_file_id=drive_file_id,
                drive_url=drive_url,
                thumbnail_url=drive_url,
                title=f"Previous Tournament - {asset_path.name}",
            ))
        elif extension in PREV_TOUR_VIDEO_EXTENSIONS and drive_file_id not in existing_video_ids:
            fallback_videos.append(SimpleNamespace(
                drive_file_id=drive_file_id,
                drive_url=drive_url,
                thumbnail_url="",
                title=f"Previous Tournament Video - {asset_path.name}",
            ))

    return fallback_photos, fallback_videos


def _fetch_soundcloud_search_results(query: str, limit: int = 10) -> list[dict]:
    """Fetch accurate SoundCloud track search results via the public web client API."""
    if not query:
        return []

    user_agent = "Mozilla/5.0"
    client_id = _get_soundcloud_client_id()
    search_url = "https://api-v2.soundcloud.com/search/tracks?" + urlencode(
        {
            "q": query,
            "client_id": client_id,
            "limit": limit,
        }
    )
    search_request = Request(search_url, headers={"User-Agent": user_agent})
    payload = json.loads(urlopen(search_request, timeout=15).read().decode("utf-8"))

    results: list[dict] = []

    for item in payload.get("collection", []):
        if item.get("kind") != "track":
            continue
        if item.get("embeddable_by") != "all":
            continue
        if item.get("policy") != "ALLOW" or item.get("state") != "finished":
            continue

        artwork_url = item.get("artwork_url") or item.get("user", {}).get("avatar_url") or ""
        if artwork_url:
            artwork_url = artwork_url.replace("-large", "-t300x300")

        results.append({
            "url": item.get("permalink_url") or "",
            "title": item.get("title") or "",
            "artist": item.get("user", {}).get("username") or "",
            "artist_url": item.get("user", {}).get("permalink_url") or "",
            "artwork_url": artwork_url,
            "waveform_url": item.get("waveform_url") or "",
            "duration_ms": item.get("duration") or 0,
        })

    return results


@require_GET
def api_soundcloud_search(request):
    """Return lightweight SoundCloud search results for the registration modal."""
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"success": True, "results": []})

    try:
        results = _fetch_soundcloud_search_results(query)
    except Exception:
        logger.exception("SoundCloud search failed")
        return JsonResponse(
            {"success": False, "error": "SoundCloud search is unavailable right now."},
            status=502,
        )

    return JsonResponse({"success": True, "results": results})


def _split_full_name(full_name):
    name = (full_name or "").strip()
    if not name:
        return "", ""
    parts = name.split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _mask_email(email):
    if not email or "@" not in email:
        return email
    local_part, domain = email.split("@", 1)
    visible = local_part[:1] or "*"
    return f"{visible}****@{domain}"


def _set_roster_session(request, team):
    request.session["_roster_team_id"] = team.pk
    request.session["_roster_code"] = team.roster_code


def _clear_roster_session(request):
    request.session.pop("_roster_team_id", None)
    request.session.pop("_roster_code", None)


def _get_authenticated_roster_team(request):
    team_id = request.session.get("_roster_team_id")
    code = request.session.get("_roster_code")
    if not team_id or not code:
        return None

    try:
        team = Team.objects.get(pk=int(team_id))
    except (Team.DoesNotExist, ValueError):
        _clear_roster_session(request)
        return None

    if not team.roster_code or team.roster_code != code:
        _clear_roster_session(request)
        return None

    return team


def _build_roster_access_link(request, team):
    signer = signing.TimestampSigner(salt=ROSTER_ACCESS_SALT)
    token = signer.sign(f"{team.pk}:{team.roster_code}")
    query = urlencode({"access": token})
    return request.build_absolute_uri(f"{reverse('roster_update')}?{query}")


def _authenticate_roster_token(request, token):
    signer = signing.TimestampSigner(salt=ROSTER_ACCESS_SALT)
    try:
        value = signer.unsign(token, max_age=ROSTER_ACCESS_MAX_AGE)
    except signing.BadSignature:
        return None

    try:
        team_id, code = value.split(":", 1)
        team = Team.objects.get(pk=int(team_id))
    except (ValueError, Team.DoesNotExist):
        return None

    if not code or team.roster_code != code:
        return None

    _set_roster_session(request, team)
    return team


def _collect_profile_roster_rows(request, team):
    player_ids = request.POST.getlist("player_id")
    player_firsts = request.POST.getlist("player_first")
    player_lasts = request.POST.getlist("player_last")
    player_deletes = request.POST.getlist("player_delete")
    row_count = max(
        len(player_ids),
        len(player_firsts),
        len(player_lasts),
        len(player_deletes),
    )
    existing_players = {str(player.pk): player for player in team.players.all()}
    rows = []

    for index in range(row_count):
        player_id = player_ids[index].strip() if index < len(player_ids) else ""
        first_name = player_firsts[index].strip() if index < len(player_firsts) else ""
        last_name = player_lasts[index].strip() if index < len(player_lasts) else ""
        delete_flag = player_deletes[index] if index < len(player_deletes) else "0"
        player = existing_players.get(player_id)

        if delete_flag == "1" or (player and not first_name and not last_name):
            if player:
                rows.append({"action": "delete", "player": player})
            continue

        if not first_name and not last_name:
            continue

        if not first_name or not last_name:
            raise ValueError("rp.msg_profile_player_name")

        rows.append({
            "action": "upsert",
            "player": player,
            "first_name": first_name,
            "last_name": last_name,
        })

    if sum(1 for row in rows if row["action"] == "upsert") < ROSTER_MIN_PLAYERS:
        raise ValueError("rp.msg_min_players")

    return rows


def _save_roster_profile(request, team):
    team_name = request.POST.get("team_name", "").strip()
    captain_name = request.POST.get("captain_name", "").strip()
    captain_email = request.POST.get("captain_email", "").strip()
    captain_phone = request.POST.get("captain_phone", "").strip()
    
    entrance_url = request.POST.get("entranceUrl", "").strip() or None
    entrance_title = request.POST.get("entranceTitle", "").strip() or None
    entrance_artist = request.POST.get("entranceArtist", "").strip() or None
    entrance_artwork_url = request.POST.get("entranceArtworkUrl", "").strip() or None

    if not team_name:
        raise ValueError("rp.msg_profile_team")
    if not captain_name:
        raise ValueError("rp.msg_profile_captain")
    if not captain_email:
        raise ValueError("rp.msg_profile_email")
    if not captain_phone:
        raise ValueError("rp.msg_profile_phone")

    if Team.objects.exclude(pk=team.pk).filter(name__iexact=team_name).exists():
        raise ValueError("rp.msg_profile_team_conflict")
    if Team.objects.exclude(pk=team.pk).filter(cap_email__iexact=captain_email).exists():
        raise ValueError("rp.msg_profile_email_conflict")
    if Team.objects.exclude(pk=team.pk).filter(cap_phone=captain_phone).exists():
        raise ValueError("rp.msg_profile_phone_conflict")

    roster_rows = _collect_profile_roster_rows(request, team)
    cap_name, cap_surname = _split_full_name(captain_name)
    logo_file = request.FILES.get("logo")

    with transaction.atomic():
        team.name = team_name
        team.cap_name = cap_name
        team.cap_surname = cap_surname
        team.cap_email = captain_email
        team.cap_phone = captain_phone
        
        team.entrance_url = entrance_url
        team.entrance_title = entrance_title
        team.entrance_artist = entrance_artist
        team.entrance_artwork_url = entrance_artwork_url
        
        entrance_start_seconds_raw = request.POST.get("entranceStartSeconds", "0")
        try:
            team.entrance_start_seconds = int(entrance_start_seconds_raw)
        except ValueError:
            team.entrance_start_seconds = 0
            
        team.entrance_source = request.POST.get("entranceSource", "soundcloud")
        
        team.save(
            update_fields=["name", "cap_name", "cap_surname", "cap_email", "cap_phone", 
                           "entrance_url", "entrance_title", "entrance_artist", "entrance_artwork_url",
                           "entrance_start_seconds", "entrance_source"]
        )

        for row in roster_rows:
            if row["action"] == "delete":
                row["player"].delete()
                continue

            player = row["player"]
            if player:
                player.first_name = row["first_name"]
                player.last_name = row["last_name"]
                player.save(update_fields=["first_name", "last_name"])
            else:
                team.players.create(
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                )

        if logo_file:
            save_team_logo(team, upload_file=logo_file)

    return team


def index(request):
    """Landing page with live slot counter."""
    from .constants import REGISTRATION_CLOSED, REGISTRATION_DEADLINE_ISO, FAN_VOTING_ENABLED
    
    # Allow hiding voting via query param ?hide_voting=1
    hide_voting = request.GET.get('hide_voting') == '1'
    voting_enabled = FAN_VOTING_ENABLED and not hide_voting

    available = get_available_slots()

    # Teams with confirmed vote count, sorted by votes DESC, then by name
    from django.db.models import Count, Q
    teams = Team.objects.annotate(
        confirmed_votes=Count('fan_votes', filter=Q(fan_votes__confirmed_at__isnull=False))
    ).order_by('-confirmed_votes', 'name')
    
    # Calculate total confirmed votes for progress bars
    total_votes = sum(t.confirmed_votes for t in teams)
    max_votes = max((t.confirmed_votes for t in teams), default=1)
    
    context = {
        "available_slots": available,
        "registered_teams": MAX_TOURNAMENT_SLOTS - available,
        "max_slots": MAX_TOURNAMENT_SLOTS,
        "teams": teams,
        "total_votes": total_votes,
        "max_votes": max_votes,
        "registration_closed": REGISTRATION_CLOSED,
        "registration_deadline": REGISTRATION_DEADLINE_ISO,
        "voting_enabled": voting_enabled,
    }
    return render(request, "tournament/index.html", context)


def tournament_hub(request):
    """Match Centre placeholder page until event start."""
    context = {
        "page_title": "Match Centre | Pocket Aces Court cup 2",
        "page_description": "Match Centre opens on June 6, 2026 at 09:00 for Pocket Aces Court cup 2.",
        "unlock_iso": "2026-06-06T09:00:00+02:00",
    }
    return render(request, "tournament/match_coming_soon.html", context)


def tournament_teams(request):
    """Legacy teams page now redirects to the registration-first landing page."""
    return redirect("index")


def tournament_match(request, match_id):
    """Legacy match page now redirects to Match Centre placeholder."""
    return redirect("tournament_hub")


def tournament_team(request, team_id):
    """Public team profile showing roster, logo, and entrance song."""
    team = get_object_or_404(Team, id=team_id)
    return render(request, "tournament/team_detail.html", {"team": team})


def tournament_player(request, player_id):
    """Legacy player stats page now redirects to the registration-first landing page."""
    return redirect("index")


def tournament_gallery(request):
    """Public gallery page — photos grid + video cards, with optional filters."""
    team_filter = request.GET.get("team", "")
    match_filter = request.GET.get("match", "")

    photos = GalleryPhoto.objects.order_by("order", "-uploaded_at")
    videos = GalleryVideo.objects.order_by("order", "-uploaded_at")

    if team_filter:
        photos = photos.filter(team_id=team_filter)
        videos = videos.filter(team_id=team_filter)
    if match_filter:
        photos = photos.filter(match_id=match_filter)
        videos = videos.filter(match_id=match_filter)

    # Group by tournament
    # Current tournament media (empty tag or '2026-cup')
    # Previous tournament media ('prev-tour')
    current_photos = photos.exclude(tournament_tag='prev-tour')
    current_videos = videos.exclude(tournament_tag='prev-tour')
    
    prev_photos = list(photos.filter(tournament_tag='prev-tour'))
    prev_videos = list(videos.filter(tournament_tag='prev-tour'))

    if not team_filter and not match_filter:
        fallback_prev_photos, fallback_prev_videos = _build_prev_tour_static_media(
            {photo.drive_file_id for photo in prev_photos},
            {video.drive_file_id for video in prev_videos},
        )
        prev_photos.extend(fallback_prev_photos)
        prev_videos.extend(fallback_prev_videos)

    # Build filter options
    teams_with_media = (
        Team.objects.filter(
            db_models.Q(gallery_photos__isnull=False) | db_models.Q(gallery_videos__isnull=False)
        ).distinct().order_by("name")
    )
    matches_with_media = (
        Match.objects.filter(
            db_models.Q(gallery_photos__isnull=False) | db_models.Q(gallery_videos__isnull=False)
        ).distinct().select_related("team_a", "team_b").order_by("match_number")
    )

    return render(request, "tournament/gallery.html", {
        "active": "gallery",
        "photos": current_photos,
        "videos": current_videos,
        "prev_photos": prev_photos,
        "prev_videos": prev_videos,
        "teams_with_media": teams_with_media,
        "matches_with_media": matches_with_media,
        "team_filter": team_filter,
        "match_filter": match_filter,
        "page_title": "Gallery | Pocket Aces Court cup 2",
        "page_description": "Photos and video highlights from Pocket Aces Court cup 2.",
    })


def api_live_scores(request):
    """JSON endpoint — returns all matches with current scores for auto-refresh."""
    matches = (
        Match.objects
        .select_related("team_a", "team_b")
        .order_by("start_time", "court")
    )
    data = []
    for m in matches:
        data.append({
            "id": m.pk,
            "match_number": m.match_number,
            "team_a": m.display_name_a,
            "team_b": m.display_name_b,
            "score_a": m.score_a,
            "score_b": m.score_b,
            "status": m.status,
            "status_display": m.get_status_display(),
        })
    return JsonResponse({"matches": data})

@ensure_csrf_cookie
def register(request):
    """Registration form page (renders the empty form + CSRF cookie)."""
    from .constants import REGISTRATION_CLOSED
    if REGISTRATION_CLOSED:
        return redirect('index')
    return render(request, "tournament/register.html")




@require_POST
def api_register_team(request):
    """
    JSON endpoint: validate and create a team.

    Returns
    -------
    JsonResponse  {success: bool, team_id?: int, error?: str}
    """
    from .constants import REGISTRATION_CLOSED
    if REGISTRATION_CLOSED:
        return JsonResponse(
            {"success": False, "error": "Registration is closed."}, status=403
        )
    try:
        data, players_data, logo_file = _parse_registration_payload(request)
    except ValueError as exc:
        return JsonResponse(
            {"success": False, "error": str(exc)}, status=400
        )

    form = TeamRegistrationForm(data)
    if not form.is_valid():
        # Return the first validation error
        first_error = next(iter(form.errors.values()))[0]
        return JsonResponse({"success": False, "error": first_error}, status=400)


    try:
        with transaction.atomic():
            team = register_team(form.cleaned_data, players_data=players_data)
            if logo_file:
                save_team_logo(team, upload_file=logo_file)

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
                subject = "Pocket Aces Court cup 2 - Instrukcje platnosci"
                message = (
                    f"Dziekujemy za rejestracje druzyny {team.name} na Pocket Aces Court cup 2.\n\n"
                    "Aby dokonczyc rejestracje, prosimy o oplate wpisowego 150 zl na ponizszy numer BLIK:\n"
                    f"BLIK: {blik}\n"
                    f"TytuÅ‚: {team.name}\n\n"
                    "W razie pytan odpowiedz na tego maila.\n\n"
                    "Do zobaczenia na boisku!\n\n"
                    "Pocket Aces Sports Club\n"
                )
            else:
                subject = "Pocket Aces Court cup 2 - Payment Instructions"
                message = (
                    f"Thank you for registering {team.name} for Pocket Aces Court cup 2.\n\n"
                    "To complete your registration, please send the 150 zl entry fee to the following BLIK number:\n"
                    f"BLIK: {blik}\n"
                    f"Title: Pocket Aces Court cup 2 - {team.name}\n\n"
                    "If you have any questions, reply to this email.\n\n"
                    "See you on the court!\n\n"
                    "Pocket Aces Sports Club\n"
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

@require_POST
def api_vote_team(request):
    """
    JSON endpoint: vote for a team with email confirmation.
    """
    from .constants import FAN_VOTING_ENABLED

    if not FAN_VOTING_ENABLED:
        return JsonResponse({'success': False, 'error': 'Fan voting is currently disabled.'}, status=403)

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        team_id = data.get('team_id')
        
        if not email or not team_id:
             return JsonResponse({'success': False, 'error': 'Email and team are required.'}, status=400)

        team = Team.objects.filter(id=team_id).first()
        if not team:
            return JsonResponse({'success': False, 'error': 'Team not found.'}, status=404)
            
        if TeamFanVote.objects.filter(email=email, confirmed_at__isnull=False).exists():
            return JsonResponse({'success': False, 'error': 'This email has already voted.'}, status=400)

        # Upsert unconfirmed vote
        vote, created = TeamFanVote.objects.update_or_create(
            email=email,
            defaults={'team': team, 'confirmed_at': None}
        )
        
        confirm_url = request.build_absolute_uri(reverse('vote_confirm', args=[vote.token]))
        
        send_mail(
            subject='Confirm your vote - Pocket Aces Court cup 2',
            message=f'Click the link below to confirm your vote for {team.name}:\n\n{confirm_url}',
            from_email=settings.DEFAULT_FROM_EMAIL, 
            recipient_list=[email], 
            fail_silently=False,
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f'Error saving vote: {e}')
        return JsonResponse({'success': False, 'error': 'Failed to process vote.'}, status=500)

def vote_confirm(request, token):
    """Confirm a fan vote via email token."""
    from django.utils.timezone import now
    try:
        vote = TeamFanVote.objects.get(token=token)
        if not vote.confirmed_at:
            vote.confirmed_at = now()
            vote.save()
        return render(request, "tournament/vote_success.html", {"team": vote.team})
    except TeamFanVote.DoesNotExist:
        return render(request, "tournament/vote_error.html", {"error": "Invalid or expired voting link."})


# â”€â”€ Captain Roster Update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@ensure_csrf_cookie
def roster_update_view(request):
    """
    Public page where captains manage the team profile and roster.
    """
    import random
    from .constants import ROSTER_CODE_LENGTH

    teams = Team.objects.order_by("name")
    error = ""
    error_key = ""
    success = ""
    success_key = ""
    authenticated_team = None
    players = None
    # Which team was selected (to show code-entry step)
    code_sent_team = None
    masked_email = ""
    # Language from frontend (localStorage synced via hidden field)
    ui_lang = request.POST.get("lang", "en") if request.method == "POST" else "en"

    if request.method == "GET" and request.GET.get("reset"):
        _clear_roster_session(request)

    if request.method == "GET":
        access_token = request.GET.get("access", "").strip()
        if access_token:
            authenticated_team = _authenticate_roster_token(request, access_token)
            if authenticated_team:
                players = authenticated_team.players.all().order_by("pk")
            else:
                error_key = "rp.msg_link_invalid"
                error = ROSTER_MESSAGE_DEFAULTS[error_key]

        if not authenticated_team:
            authenticated_team = _get_authenticated_roster_team(request)
            if authenticated_team:
                players = authenticated_team.players.all().order_by("pk")

    if request.method == "POST":
        action = request.POST.get("action", "")
        team_id = request.POST.get("team_id", "")

        if action == "select_team":
            # â”€â”€ Step 1: Generate code and email it to captain â”€â”€
            if not team_id:
                error = "Please select a team."
                error_key = "rp.msg_select_team"
            else:
                try:
                    team = Team.objects.get(pk=int(team_id))
                except (Team.DoesNotExist, ValueError):
                    error = "Team not found."
                    error_key = "rp.msg_team_not_found"
                    team = None

                if team:
                    code = "".join(
                        random.choices("0123456789", k=ROSTER_CODE_LENGTH)
                    )
                    team.roster_code = code
                    team.save(update_fields=["roster_code"])
                    request.session["_roster_team_id"] = team.pk
                    request.session.pop("_roster_code", None)
                    access_url = _build_roster_access_link(request, team)

                    # Build email in the user's language
                    if ui_lang == "pl":
                        email_subject = "Pocket Aces Court cup 2 - Dostep do profilu druzyny"
                        email_body = (
                            f"Czesc {team.cap_name},\n\n"
                            f"Otworz ten link, aby zarzadzac profilem druzyny \"{team.name}\":\n"
                            f"{access_url}\n\n"
                            f"Jesli wolisz wpisac kod recznie, uzyj: {code}\n\n"
                            "Po zalogowaniu mozesz edytowac sklad, dane kapitana i logo.\n\n"
                            "- Pocket Aces Court cup 2"
                        )
                    else:
                        email_subject = "Pocket Aces Court cup 2 - Team Profile Access"
                        email_body = (
                            f"Hi {team.cap_name},\n\n"
                            f"Open this link to manage team \"{team.name}\":\n"
                            f"{access_url}\n\n"
                            f"If you prefer the manual code flow, use: {code}\n\n"
                            "Once inside, you can edit the roster, captain details, and logo.\n\n"
                            "- Pocket Aces Court cup 2"
                        )

                    try:
                        send_mail(
                            subject=email_subject,
                            message=email_body,
                            from_email=None,  # uses DEFAULT_FROM_EMAIL
                            recipient_list=[team.cap_email],
                        )
                    except Exception:
                        logger.exception("Failed to send roster code email")
                        error = "Failed to send email. Please try again or contact the organizer."
                        error_key = "rp.msg_email_fail"
                    else:
                        masked_email = _mask_email(team.cap_email)
                        success = f"Code sent to {masked_email}"
                        success_key = "rp.msg_code_sent"
                        code_sent_team = team

        elif action == "auth":
            # â”€â”€ Step 2: Verify code entered by captain â”€â”€
            code = request.POST.get("code", "").strip()
            sess_team_id = request.session.get("_roster_team_id")
            if not sess_team_id:
                error = "Session expired. Please start over."
                error_key = "rp.msg_session_expired"
            elif not code:
                error = "Please enter the access code."
                error_key = "rp.msg_enter_code"
            else:
                try:
                    team = Team.objects.get(pk=int(sess_team_id))
                except (Team.DoesNotExist, ValueError):
                    error = "Team not found."
                    error_key = "rp.msg_team_not_found"
                    team = None

                if team:
                    if not team.roster_code:
                        error = "No code has been generated. Please start over."
                        error_key = "rp.msg_no_code"
                    elif team.roster_code != code:
                        error = "Incorrect code. Please check your email and try again."
                        error_key = "rp.msg_wrong_code"
                        code_sent_team = team  # stay on code-entry step
                    else:
                        _set_roster_session(request, team)
                        authenticated_team = team
                        players = team.players.all().order_by("pk")

        elif action == "save":
            team = _get_authenticated_roster_team(request)
            if not team:
                error = "Session expired. Please authenticate again."
                error_key = "rp.msg_session_expired"
            else:
                if request.POST.getlist("player_first") or request.POST.get("team_name"):
                    try:
                        team = _save_roster_profile(request, team)
                    except ValueError as exc:
                        error_key = str(exc)
                        error = ROSTER_MESSAGE_DEFAULTS.get(error_key, str(exc))
                    else:
                        success_key = "rp.msg_profile_saved"
                        success = ROSTER_MESSAGE_DEFAULTS[success_key]
                else:
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
                        valid_positions = {"S", "OH", "MB", "OPP", "L"}
                        player.position = position_raw if position_raw in valid_positions else ""
                        player.save(update_fields=["jersey_number", "position"])

                    success = "Roster updated successfully!"
                    success_key = "rp.msg_roster_saved"

                authenticated_team = team
                players = team.players.all().order_by("pk")

        elif action == "upload_logo":
            team = _get_authenticated_roster_team(request)
            if not team:
                error = "Session expired. Please authenticate again."
                error_key = "rp.msg_session_expired"
            else:
                logo_file = request.FILES.get("logo")
                if not logo_file:
                    error = "Please select an image file."
                    error_key = "rp.msg_select_file"
                else:
                    try:
                        save_team_logo(team, upload_file=logo_file)
                    except ValueError as exc:
                        error = str(exc)
                        if "Maximum size" in error:
                            error_key = "rp.msg_file_too_large"
                        else:
                            error_key = "rp.msg_file_type"
                    else:
                        success = "Logo uploaded successfully!"
                        success_key = "rp.msg_logo_saved"

                authenticated_team = team
                players = team.players.all().order_by("pk")

        if not authenticated_team:
            authenticated_team = _get_authenticated_roster_team(request)
            if authenticated_team:
                players = authenticated_team.players.all().order_by("pk")

    return render(request, "tournament/roster_update.html", {
        "teams": teams,
        "error": error,
        "error_key": error_key,
        "success": success,
        "success_key": success_key,
        "masked_email": masked_email,
        "authenticated_team": authenticated_team,
        "code_sent_team": code_sent_team,
        "players": players,
        "MEDIA_URL": settings.MEDIA_URL,
    })
