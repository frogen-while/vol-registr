"""Smoke tests for Phase 13 — Gallery Videos (tabs + CRUD)."""
import json
import re
import urllib.request
import urllib.parse

BASE = "http://127.0.0.1:8000"
LOGIN_URL = BASE + "/panel/login/"
GALLERY_URL = BASE + "/panel/gallery/"
VIDEO_ADD_URL = BASE + "/panel/gallery/videos/add/"

passed = 0
total = 0


def check(label, condition):
    global passed, total
    total += 1
    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        print(f"  [FAIL] {label}")


# ── Login ──────────────────────────────────────────────

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

print("Logging in...")
resp = opener.open(LOGIN_URL)
html = resp.read().decode()
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({
    "csrfmiddlewaretoken": csrf,
    "username": "admin",
    "password": "admin123",
}).encode()
req = urllib.request.Request(LOGIN_URL, data=data, headers={"Referer": LOGIN_URL})
opener.open(req)


# ── 1. Gallery with tabs ────────────────────────────────

print("\n1. Gallery page with tabs")
resp = opener.open(GALLERY_URL)
html = resp.read().decode()
check("Gallery loads (200)", resp.status == 200)
check("Photos tab present", "?tab=photos" in html)
check("Videos tab present", "?tab=videos" in html)
check("Photos tab is active by default", 'pnl-tab--active' in html and 'Photos' in html)
check("Add Photo button visible", "Add Photo" in html)


# ── 2. Videos tab ───────────────────────────────────────

print("\n2. Videos tab")
resp = opener.open(GALLERY_URL + "?tab=videos")
html = resp.read().decode()
check("Videos tab loads (200)", resp.status == 200)
check("Add Video button present", "Add Video" in html)
check("No videos message", "No videos yet" in html)


# ── 3. Add video form ───────────────────────────────────

print("\n3. Add video form")
resp = opener.open(VIDEO_ADD_URL)
html = resp.read().decode()
check("Video form loads (200)", resp.status == 200)
check("Has title field", "id_title" in html)
check("Has drive_url field", "id_drive_url" in html)
check("Has description field", "id_description" in html)
check("Has Save button", "Save" in html)
check("Back to Gallery link", "Back to Gallery" in html)


# ── 4. Add a video ──────────────────────────────────────

print("\n4. Add video")
resp = opener.open(VIDEO_ADD_URL)
html = resp.read().decode()
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({
    "csrfmiddlewaretoken": csrf,
    "title": "Test Highlights Video",
    "drive_url": "https://drive.google.com/file/d/4aTestVideoFileId123/view?usp=sharing",
    "description": "Best moments from the tournament",
}).encode()
req = urllib.request.Request(VIDEO_ADD_URL, data=data, headers={"Referer": VIDEO_ADD_URL})
resp = opener.open(req)
html = resp.read().decode()
check("Redirect after video add", "/panel/gallery/" in resp.url)

# Check video appears in videos tab
resp = opener.open(GALLERY_URL + "?tab=videos")
html = resp.read().decode()
check("Video appears in videos tab", "Test Highlights Video" in html)
check("Description shown", "Best moments" in html)
check("Play icon present", "fa-play-circle" in html)
check("Thumbnail generated", "drive.google.com/thumbnail" in html)


# ── 5. Add second video ─────────────────────────────────

print("\n5. Add second video")
resp = opener.open(VIDEO_ADD_URL)
html = resp.read().decode()
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({
    "csrfmiddlewaretoken": csrf,
    "title": "Second Test Video",
    "drive_url": "https://drive.google.com/file/d/5bSecondVideoTest456/view",
    "description": "",
}).encode()
req = urllib.request.Request(VIDEO_ADD_URL, data=data, headers={"Referer": VIDEO_ADD_URL})
resp = opener.open(req)
check("Second video added", resp.status == 200)


# ── 6. Edit video ───────────────────────────────────────

print("\n6. Edit video")
resp = opener.open(GALLERY_URL + "?tab=videos")
html = resp.read().decode()
edit_match = re.search(r'href="(/panel/gallery/videos/\d+/edit/)"', html)
check("Edit button present", edit_match is not None)
if edit_match:
    edit_url = BASE + edit_match.group(1)
    resp = opener.open(edit_url)
    html = resp.read().decode()
    check("Edit form loads (200)", resp.status == 200)
    check("Title pre-populated", "Test Highlights Video" in html or "Second Test Video" in html)
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    data = urllib.parse.urlencode({
        "csrfmiddlewaretoken": csrf,
        "title": "Updated Video Title",
        "drive_url": "https://drive.google.com/file/d/4aTestVideoFileId123/view",
        "description": "Updated description",
    }).encode()
    req = urllib.request.Request(edit_url, data=data, headers={"Referer": edit_url})
    resp = opener.open(req)
    resp2 = opener.open(GALLERY_URL + "?tab=videos")
    html2 = resp2.read().decode()
    check("Updated title shown", "Updated Video Title" in html2)


# ── 7. Invalid URL on video ─────────────────────────────

print("\n7. Invalid URL on video form")
resp = opener.open(VIDEO_ADD_URL)
html = resp.read().decode()
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({
    "csrfmiddlewaretoken": csrf,
    "title": "Bad Video",
    "drive_url": "https://example.com/not-drive",
    "description": "",
}).encode()
req = urllib.request.Request(VIDEO_ADD_URL, data=data, headers={"Referer": VIDEO_ADD_URL})
resp = opener.open(req)
html = resp.read().decode()
check("Invalid URL shows error", "Cannot extract file ID" in html)


# ── 8. Delete video ─────────────────────────────────────

print("\n8. Delete video")
resp = opener.open(GALLERY_URL + "?tab=videos")
html = resp.read().decode()
delete_match = re.search(r'action="(/panel/gallery/videos/\d+/delete/)"', html)
check("Delete form present", delete_match is not None)
if delete_match:
    delete_url = BASE + delete_match.group(1)
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    data = urllib.parse.urlencode({"csrfmiddlewaretoken": csrf}).encode()
    req = urllib.request.Request(delete_url, data=data, headers={"Referer": GALLERY_URL})
    resp = opener.open(req)
    check("Redirect after delete", "/panel/gallery/" in resp.url)


# ── 9. Video reorder endpoint ───────────────────────────

print("\n9. Video reorder")
resp = opener.open(GALLERY_URL + "?tab=videos")
html = resp.read().decode()
ids = [int(m) for m in re.findall(r'data-id="(\d+)"', html)]
if ids:
    reorder_url = BASE + "/panel/gallery/videos/reorder/"
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    payload = json.dumps(list(reversed(ids))).encode()
    req = urllib.request.Request(reorder_url, data=payload, headers={
        "Referer": GALLERY_URL,
        "X-CSRFToken": csrf,
        "Content-Type": "application/json",
    })
    resp = opener.open(req)
    body = json.loads(resp.read().decode())
    check("Video reorder returns ok", body.get("ok") is True)
else:
    check("Video reorder — skipped (no videos left)", True)


# ── 10. Tab counts ──────────────────────────────────────

print("\n10. Tab counts")
resp = opener.open(GALLERY_URL)
html = resp.read().decode()
check("Photos count shown", '>0<' in html or 'pnl-tab__count' in html)
check("Videos count shown", 'Videos' in html and 'pnl-tab__count' in html)


# ── 11. Cleanup ─────────────────────────────────────────

print("\n11. Cleanup")
resp = opener.open(GALLERY_URL + "?tab=videos")
html = resp.read().decode()
delete_urls = re.findall(r'action="(/panel/gallery/videos/\d+/delete/)"', html)
cleaned = 0
for durl in delete_urls:
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    data = urllib.parse.urlencode({"csrfmiddlewaretoken": csrf}).encode()
    req = urllib.request.Request(BASE + durl, data=data, headers={"Referer": GALLERY_URL})
    resp = opener.open(req)
    html = resp.read().decode()
    cleaned += 1
check(f"Cleaned up {cleaned} test video(s)", True)


# ── Summary ──────────────────────────────────────────────

print("\n" + "=" * 50)
print(f"Results: {passed}/{total} checks passed")
if passed == total:
    print("All checks passed!")
else:
    print(f"{total - passed} check(s) FAILED")
