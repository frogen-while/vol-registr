"""Player CRUD — list, create, edit, delete with photo upload."""

import os
import uuid
import urllib.request
import urllib.error

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..constants import POSITION_CHOICES
from ..models import Player, PlayerMatchStats, Team

_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _save_player_photo(player, upload_file=None, photo_url=None):
    """Save a player photo from file upload or URL."""
    dest_dir = os.path.join(settings.MEDIA_ROOT, "player_photos")
    os.makedirs(dest_dir, exist_ok=True)

    if upload_file:
        ext = os.path.splitext(upload_file.name)[1].lower()
        if ext not in _PHOTO_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "wb") as f:
            for chunk in upload_file.chunks():
                f.write(chunk)
        player.photo_path = f"player_photos/{filename}"
        player.save(update_fields=["photo_path"])
        return

    if photo_url:
        req = urllib.request.Request(photo_url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)  # noqa: S310
        content_type = resp.headers.get("Content-Type", "")
        ext_map = {
            "image/jpeg": ".jpg", "image/png": ".png",
            "image/gif": ".gif", "image/webp": ".webp",
        }
        ext = ext_map.get(content_type.split(";")[0].strip(), "")
        if not ext:
            raise ValueError("Unsupported image type from URL")
        filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "wb") as f:
            f.write(resp.read())
        player.photo_path = f"player_photos/{filename}"
        player.save(update_fields=["photo_path"])


@staff_member_required(login_url="/panel/login/")
def players_list_view(request):
    """List all players with search and team filter."""
    q = request.GET.get("q", "").strip()
    team_id = request.GET.get("team", "")
    players = Player.objects.select_related("team").order_by("team__name", "last_name", "first_name")
    if q:
        players = players.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(jersey_number__icontains=q) | Q(team__name__icontains=q)
        )
    if team_id:
        players = players.filter(team_id=team_id)
    teams = Team.objects.order_by("name")
    return render(request, "panel/players_list.html", {
        "page_title": "Players",
        "nav_section": "players",
        "players": players,
        "teams": teams,
        "q": q,
        "team_filter": team_id,
        "positions": dict(POSITION_CHOICES),
    })


@staff_member_required(login_url="/panel/login/")
def player_detail_view(request, pk):
    """Player detail with match-by-match stats."""
    player = get_object_or_404(Player.objects.select_related("team"), pk=pk)
    match_stats = (
        PlayerMatchStats.objects.filter(player=player)
        .select_related("match", "match__team_a", "match__team_b")
        .order_by("match__start_time")
    )
    # Aggregate totals
    from django.db.models import Sum
    totals = PlayerMatchStats.objects.filter(player=player).aggregate(
        total_kills=Sum("kills"),
        total_aces=Sum("aces"),
        total_blocks=Sum("blocks"),
        total_assists=Sum("assists"),
        total_serve_errors=Sum("serve_errors"),
        total_attack_errors=Sum("attack_errors"),
        total_sets_played=Sum("sets_played"),
    )
    total_points = (totals["total_kills"] or 0) + (totals["total_aces"] or 0) + (totals["total_blocks"] or 0)
    return render(request, "panel/player_detail.html", {
        "page_title": f"{player.first_name} {player.last_name}",
        "nav_section": "players",
        "player": player,
        "match_stats": match_stats,
        "totals": totals,
        "total_points": total_points,
        "matches_count": match_stats.count(),
    })


@staff_member_required(login_url="/panel/login/")
def player_create_view(request):
    """Create a new player."""
    teams = Team.objects.order_by("name")
    if request.method == "POST":
        team_id = request.POST.get("team")
        team = get_object_or_404(Team, pk=team_id)
        player = Player(
            team=team,
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            jersey_number=request.POST.get("jersey_number", "").strip(),
            position=request.POST.get("position", ""),
        )
        player.save()
        # Handle photo
        photo_file = request.FILES.get("photo_file")
        photo_url = request.POST.get("photo_url", "").strip()
        try:
            if photo_file:
                _save_player_photo(player, upload_file=photo_file)
            elif photo_url:
                _save_player_photo(player, photo_url=photo_url)
        except Exception as e:
            messages.warning(request, f"Player saved but photo failed: {e}")
        messages.success(request, f"Player {player} created.")
        return redirect("panel:players")
    return render(request, "panel/player_form.html", {
        "page_title": "Add Player",
        "nav_section": "players",
        "teams": teams,
        "positions": POSITION_CHOICES,
    })


@staff_member_required(login_url="/panel/login/")
def player_edit_view(request, pk):
    """Edit an existing player."""
    player = get_object_or_404(Player.objects.select_related("team"), pk=pk)
    teams = Team.objects.order_by("name")
    if request.method == "POST":
        team_id = request.POST.get("team")
        player.team = get_object_or_404(Team, pk=team_id)
        player.first_name = request.POST.get("first_name", "").strip()
        player.last_name = request.POST.get("last_name", "").strip()
        player.jersey_number = request.POST.get("jersey_number", "").strip()
        player.position = request.POST.get("position", "")
        player.save()
        # Handle photo
        photo_file = request.FILES.get("photo_file")
        photo_url = request.POST.get("photo_url", "").strip()
        remove_photo = request.POST.get("remove_photo")
        try:
            if remove_photo and not photo_file and not photo_url:
                player.photo_path = ""
                player.save(update_fields=["photo_path"])
            elif photo_file:
                _save_player_photo(player, upload_file=photo_file)
            elif photo_url:
                _save_player_photo(player, photo_url=photo_url)
        except Exception as e:
            messages.warning(request, f"Player saved but photo failed: {e}")
        messages.success(request, f"Player {player} updated.")
        return redirect("panel:players")
    return render(request, "panel/player_form.html", {
        "page_title": "Edit Player",
        "nav_section": "players",
        "teams": teams,
        "positions": POSITION_CHOICES,
        "player": player,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def player_delete_view(request, pk):
    """Delete a player."""
    player = get_object_or_404(Player, pk=pk)
    name = str(player)
    player.delete()
    messages.success(request, f"Player {name} deleted.")
    return redirect("panel:players")
