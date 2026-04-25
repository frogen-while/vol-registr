import os
import urllib.error
import urllib.request
import uuid

from django.conf import settings


_ALLOWED_TEAM_LOGO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
_ALLOWED_TEAM_LOGO_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}
_MAX_TEAM_LOGO_BYTES = 5 * 1024 * 1024


def save_team_logo(team, upload_file=None, logo_url=None):
    """Save a team logo from an upload or a direct image URL."""
    dest_dir = os.path.join(settings.MEDIA_ROOT, "team_logos")
    os.makedirs(dest_dir, exist_ok=True)

    if upload_file:
        if upload_file.size > _MAX_TEAM_LOGO_BYTES:
            raise ValueError("File too large. Maximum size is 5 MB.")

        ext = os.path.splitext(upload_file.name)[1].lower()
        if ext not in _ALLOWED_TEAM_LOGO_EXTENSIONS:
            raise ValueError("Only PNG, JPEG, WebP, GIF, or SVG files are allowed.")

        filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "wb") as handle:
            for chunk in upload_file.chunks():
                handle.write(chunk)

        team.logo_path = f"team_logos/{filename}"
        team.save(update_fields=["logo_path"])
        return team.logo_path

    if logo_url:
        try:
            request = urllib.request.Request(
                logo_url,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response = urllib.request.urlopen(request, timeout=10)  # noqa: S310
        except (urllib.error.URLError, ValueError) as exc:
            raise ValueError("Unable to download the team logo.") from exc

        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        ext = _ALLOWED_TEAM_LOGO_CONTENT_TYPES.get(content_type, "")
        if not ext:
            url_ext = os.path.splitext(logo_url.split("?", 1)[0])[1].lower()
            ext = url_ext if url_ext in _ALLOWED_TEAM_LOGO_EXTENSIONS else ".png"

        filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "wb") as handle:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                handle.write(chunk)

        team.logo_path = f"team_logos/{filename}"
        team.save(update_fields=["logo_path"])
        return team.logo_path

    return team.logo_path