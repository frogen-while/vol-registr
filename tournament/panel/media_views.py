"""Gallery — photos + videos CRUD, bulk add, drag-reorder, entity linking."""

import json
import os
import uuid

from django.conf import settings
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
def gallery_photo_edit_view(request, pk):
    """Edit title of an existing photo."""
    photo = get_object_or_404(GalleryPhoto, pk=pk)
    if request.method == "POST":
        photo.title = request.POST.get("title", "").strip()
        photo.save(update_fields=["title"])
        messages.success(request, "Photo updated.")
        return redirect("panel:gallery")
    return render(request, "panel/gallery_photo_edit.html", {
        "page_title": "Edit Photo",
        "nav_section": "gallery",
        "photo": photo,
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
    is_local = video.drive_file_id.startswith("local_")
    if is_local:
        # Local upload — simple title/description edit without Drive validation
        if request.method == "POST":
            video.title = request.POST.get("title", "").strip()
            video.description = request.POST.get("description", "").strip()
            video.save(update_fields=["title", "description"])
            messages.success(request, "Video updated.")
            return redirect("panel:gallery")
        return render(request, "panel/video_edit_local.html", {
            "page_title": "Edit Video",
            "nav_section": "gallery",
            "video": video,
        })
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


# ── Local File Upload ────────────────────────────────────

_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}


def _save_upload(file, subdir):
    """Save an uploaded file to media/<subdir>/, return relative media path."""
    dest_dir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(file.name)[1].lower()
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(dest_dir, filename)
    with open(filepath, "wb") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return f"{subdir}/{filename}"


@staff_member_required(login_url="/panel/login/")
def gallery_upload_view(request):
    """Upload photo(s) from the local computer."""
    if request.method == "POST":
        files = request.FILES.getlist("photos")
        title = request.POST.get("title", "").strip()
        if not files:
            messages.error(request, "No files selected.")
            return redirect("panel:gallery_upload")
        added = 0
        max_order = GalleryPhoto.objects.aggregate(m=Max("order"))["m"] or 0
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in _PHOTO_EXTENSIONS:
                messages.warning(request, f"Skipped {f.name} — unsupported format.")
                continue
            rel_path = _save_upload(f, "gallery/photos")
            media_url = f"{settings.MEDIA_URL}{rel_path}"
            max_order += 1
            GalleryPhoto.objects.create(
                title=title,
                drive_file_id=f"local_{uuid.uuid4().hex[:16]}",
                drive_url=media_url,
                thumbnail_url=media_url,
                order=max_order,
            )
            added += 1
        if added:
            messages.success(request, f"{added} photo(s) uploaded.")
        return redirect("panel:gallery")
    return render(request, "panel/gallery_upload.html", {
        "page_title": "Upload Photos",
        "nav_section": "gallery",
        "upload_type": "photos",
    })


@staff_member_required(login_url="/panel/login/")
def video_upload_view(request):
    """Upload video(s) from the local computer."""
    if request.method == "POST":
        files = request.FILES.getlist("videos")
        title = request.POST.get("title", "").strip()
        if not files:
            messages.error(request, "No files selected.")
            return redirect("panel:video_upload")
        added = 0
        max_order = GalleryVideo.objects.aggregate(m=Max("order"))["m"] or 0
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in _VIDEO_EXTENSIONS:
                messages.warning(request, f"Skipped {f.name} — unsupported format.")
                continue
            rel_path = _save_upload(f, "gallery/videos")
            media_url = f"{settings.MEDIA_URL}{rel_path}"
            max_order += 1
            GalleryVideo.objects.create(
                title=title,
                drive_file_id=f"local_{uuid.uuid4().hex[:16]}",
                drive_url=media_url,
                thumbnail_url="",
                order=max_order,
            )
            added += 1
        if added:
            messages.success(request, f"{added} video(s) uploaded.")
        return redirect("panel:gallery")
    return render(request, "panel/gallery_upload.html", {
        "page_title": "Upload Videos",
        "nav_section": "gallery",
        "upload_type": "videos",
    })
