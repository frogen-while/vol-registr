"""Database backup & restore views for the admin panel."""

import os
import shutil
import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


def _db_path():
    return str(settings.DATABASES["default"]["NAME"])


def _backup_dir():
    d = os.path.join(settings.BASE_DIR, "backups")
    os.makedirs(d, exist_ok=True)
    return d


@staff_member_required(login_url="/panel/login/")
def db_backup_view(request):
    """Show backup/restore page with existing backups list."""
    backup_dir = _backup_dir()
    backups = []
    for fname in sorted(os.listdir(backup_dir), reverse=True):
        if fname.endswith(".sqlite3"):
            fpath = os.path.join(backup_dir, fname)
            size_kb = os.path.getsize(fpath) / 1024
            backups.append({
                "name": fname,
                "size": f"{size_kb:.0f} KB",
                "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(fpath)),
            })
    return render(request, "panel/db_backup.html", {
        "page_title": "Database Backup/Restore",
        "nav_section": "dashboard",
        "backups": backups,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def db_backup_create(request):
    """Create a timestamped backup of the SQLite database."""
    db = _db_path()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(_backup_dir(), f"backup_{timestamp}.sqlite3")
    shutil.copy2(db, dest)
    messages.success(request, f"Backup created: backup_{timestamp}.sqlite3")
    return redirect("panel:db_backup")


@staff_member_required(login_url="/panel/login/")
def db_backup_download(request, filename):
    """Download a specific backup file."""
    # Sanitize filename to prevent path traversal
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".sqlite3"):
        return HttpResponse("Invalid file", status=400)
    fpath = os.path.join(_backup_dir(), safe_name)
    if not os.path.isfile(fpath):
        return HttpResponse("Backup not found", status=404)
    return FileResponse(
        open(fpath, "rb"),
        as_attachment=True,
        filename=safe_name,
    )


@staff_member_required(login_url="/panel/login/")
def db_download_current(request):
    """Download the current live database."""
    db = _db_path()
    if not os.path.isfile(db):
        return HttpResponse("Database not found", status=404)
    return FileResponse(
        open(db, "rb"),
        as_attachment=True,
        filename="db.sqlite3",
    )


@staff_member_required(login_url="/panel/login/")
@require_POST
def db_restore(request):
    """Restore database from an uploaded .sqlite3 file."""
    upload = request.FILES.get("db_file")
    if not upload:
        messages.error(request, "No file uploaded.")
        return redirect("panel:db_backup")

    if not upload.name.endswith(".sqlite3"):
        messages.error(request, "Only .sqlite3 files are accepted.")
        return redirect("panel:db_backup")

    # Limit size to 50MB
    if upload.size > 50 * 1024 * 1024:
        messages.error(request, "File too large (max 50 MB).")
        return redirect("panel:db_backup")

    db = _db_path()

    # Auto-backup current DB before restore
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_backup = os.path.join(_backup_dir(), f"pre_restore_{timestamp}.sqlite3")
    shutil.copy2(db, auto_backup)

    # Write new DB
    with open(db, "wb") as f:
        for chunk in upload.chunks():
            f.write(chunk)

    messages.success(
        request,
        f"Database restored from {upload.name}. "
        f"Auto-backup saved as pre_restore_{timestamp}.sqlite3"
    )
    return redirect("panel:db_backup")


@staff_member_required(login_url="/panel/login/")
@require_POST
def db_backup_delete(request, filename):
    """Delete a backup file."""
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".sqlite3"):
        return HttpResponse("Invalid file", status=400)
    fpath = os.path.join(_backup_dir(), safe_name)
    if os.path.isfile(fpath):
        os.remove(fpath)
        messages.success(request, f"Backup {safe_name} deleted.")
    else:
        messages.error(request, "Backup not found.")
    return redirect("panel:db_backup")
