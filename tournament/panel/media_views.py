"""Gallery — photos + videos CRUD, bulk add, drag-reorder, entity linking."""

import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..admin_forms import (
    GalleryBulkForm,
    GalleryPhotoForm,
    GalleryVideoForm,
    _drive_thumbnail,
    _drive_view_url,
    _parse_drive_file_id,
)
from ..models import (
    GalleryPhoto,
    GalleryVideo,
    Match,
    Team,
    MEDIA_STATE_CHOICES,
    MEDIA_STATE_INCOMING,
    MEDIA_STATE_TAGGED,
    MEDIA_STATE_LINKED,
    MEDIA_STATE_FEATURED,
)


@staff_member_required(login_url="/panel/login/")
def gallery_list_view(request):
    tab = request.GET.get("tab", "photos")
    state_filter = request.GET.get("state", "")
    photos = GalleryPhoto.objects.select_related("match", "team").order_by("order", "-uploaded_at")
    videos = GalleryVideo.objects.select_related("match", "team").order_by("order", "-uploaded_at")
    if state_filter:
        photos = photos.filter(media_state=state_filter)
        videos = videos.filter(media_state=state_filter)
    state_stats = dict(
        GalleryPhoto.objects.values_list("media_state").annotate(c=Count("id")).values_list("media_state", "c")
    )
    matches = Match.objects.order_by("match_number")
    teams = Team.objects.order_by("name")
    return render(request, "panel/gallery.html", {
        "page_title": "Gallery",
        "nav_section": "gallery",
        "photos": photos,
        "videos": videos,
        "tab": tab,
        "state_filter": state_filter,
        "state_choices": MEDIA_STATE_CHOICES,
        "state_stats": state_stats,
        "matches": matches,
        "teams": teams,
    })


@staff_member_required(login_url="/panel/login/")
def gallery_add_view(request):
    form = GalleryPhotoForm()
    if request.method == "POST":
        form = GalleryPhotoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Photo added.")
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Add Photo",
        "nav_section": "gallery",
        "form": form,
    })


@staff_member_required(login_url="/panel/login/")
def gallery_bulk_add_view(request):
    form = GalleryBulkForm()
    if request.method == "POST":
        form = GalleryBulkForm(request.POST)
        if form.is_valid():
            lines = form.cleaned_data["urls"].strip().splitlines()
            added = 0
            errors = []
            max_order = GalleryPhoto.objects.aggregate(m=Max("order"))["m"] or 0
            for line in lines:
                url = line.strip()
                if not url:
                    continue
                file_id = _parse_drive_file_id(url)
                if not file_id:
                    errors.append(f"Bad URL: {url[:60]}")
                    continue
                if GalleryPhoto.objects.filter(drive_file_id=file_id).exists():
                    errors.append(f"Duplicate: {file_id[:12]}…")
                    continue
                max_order += 1
                GalleryPhoto.objects.create(
                    drive_file_id=file_id,
                    drive_url=_drive_view_url(file_id),
                    thumbnail_url=_drive_thumbnail(file_id),
                    order=max_order,
                )
                added += 1
            if added:
                messages.success(request, f"{added} photo(s) added.")
            for err in errors:
                messages.warning(request, err)
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Bulk Add Photos",
        "nav_section": "gallery",
        "bulk_form": form,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def gallery_delete_view(request, pk):
    photo = get_object_or_404(GalleryPhoto, pk=pk)
    photo.delete()
    messages.success(request, "Photo deleted.")
    return redirect("panel:gallery")


@staff_member_required(login_url="/panel/login/")
@require_POST
def gallery_reorder_view(request):
    """AJAX endpoint — receives JSON array of photo IDs in new order."""
    try:
        order_ids = json.loads(request.body)
        if not isinstance(order_ids, list):
            return JsonResponse({"error": "Expected a list"}, status=400)
        for idx, photo_id in enumerate(order_ids):
            GalleryPhoto.objects.filter(pk=photo_id).update(order=idx)
        return JsonResponse({"ok": True})
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)


# ── Videos ───────────────────────────────────────────────


@staff_member_required(login_url="/panel/login/")
def video_add_view(request):
    form = GalleryVideoForm()
    if request.method == "POST":
        form = GalleryVideoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Video added.")
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Add Video",
        "nav_section": "gallery",
        "video_form": form,
    })


@staff_member_required(login_url="/panel/login/")
def video_edit_view(request, pk):
    video = get_object_or_404(GalleryVideo, pk=pk)
    form = GalleryVideoForm(instance=video)
    if request.method == "POST":
        form = GalleryVideoForm(request.POST, instance=video)
        if form.is_valid():
            form.save()
            messages.success(request, "Video updated.")
            return redirect("panel:gallery")
    return render(request, "panel/gallery_form.html", {
        "page_title": "Edit Video",
        "nav_section": "gallery",
        "video_form": form,
        "video": video,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def video_delete_view(request, pk):
    video = get_object_or_404(GalleryVideo, pk=pk)
    video.delete()
    messages.success(request, "Video deleted.")
    return redirect("panel:gallery")


@staff_member_required(login_url="/panel/login/")
@require_POST
def video_reorder_view(request):
    """AJAX endpoint — receives JSON array of video IDs in new order."""
    try:
        order_ids = json.loads(request.body)
        if not isinstance(order_ids, list):
            return JsonResponse({"error": "Expected a list"}, status=400)
        for idx, vid_id in enumerate(order_ids):
            GalleryVideo.objects.filter(pk=vid_id).update(order=idx)
        return JsonResponse({"ok": True})
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)


# ── Entity Linking & Media States ────────────────────────


@staff_member_required(login_url="/panel/login/")
@require_POST
def gallery_bulk_link_view(request):
    """Link selected photos to a match and/or team."""
    photo_ids = request.POST.getlist("photo_ids")
    match_id = request.POST.get("match_id") or None
    team_id = request.POST.get("team_id") or None
    if not photo_ids:
        messages.warning(request, "No photos selected.")
        return redirect("panel:gallery")
    photos = GalleryPhoto.objects.filter(pk__in=photo_ids)
    update_kwargs = {}
    if match_id:
        update_kwargs["match_id"] = int(match_id)
    if team_id:
        update_kwargs["team_id"] = int(team_id)
    if update_kwargs:
        new_state = MEDIA_STATE_LINKED
        update_kwargs["media_state"] = new_state
        photos.update(**update_kwargs)
        messages.success(request, f"{photos.count()} photo(s) linked.")
    else:
        messages.warning(request, "Select a match or team to link.")
    return redirect("panel:gallery")


@staff_member_required(login_url="/panel/login/")
@require_POST
def gallery_state_change_view(request, pk):
    """Change media_state of a single photo."""
    photo = get_object_or_404(GalleryPhoto, pk=pk)
    new_state = request.POST.get("state", "")
    valid_states = [s[0] for s in MEDIA_STATE_CHOICES]
    if new_state not in valid_states:
        messages.error(request, "Invalid state.")
        return redirect("panel:gallery")
    photo.media_state = new_state
    photo.save(update_fields=["media_state"])
    messages.success(request, f"State → {new_state}.")
    return redirect("panel:gallery")


@staff_member_required(login_url="/panel/login/")
@require_POST
def video_bulk_link_view(request):
    """Link selected videos to a match and/or team."""
    video_ids = request.POST.getlist("video_ids")
    match_id = request.POST.get("match_id") or None
    team_id = request.POST.get("team_id") or None
    if not video_ids:
        messages.warning(request, "No videos selected.")
        return redirect("panel:gallery")
    videos = GalleryVideo.objects.filter(pk__in=video_ids)
    update_kwargs = {}
    if match_id:
        update_kwargs["match_id"] = int(match_id)
    if team_id:
        update_kwargs["team_id"] = int(team_id)
    if update_kwargs:
        update_kwargs["media_state"] = MEDIA_STATE_LINKED
        videos.update(**update_kwargs)
        messages.success(request, f"{videos.count()} video(s) linked.")
    else:
        messages.warning(request, "Select a match or team to link.")
    return redirect("panel:gallery")
