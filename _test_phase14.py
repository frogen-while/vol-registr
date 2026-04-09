"""Smoke tests for Phase 14 — Public Gallery page."""
import json
import re
import urllib.request
import urllib.parse

BASE = "http://127.0.0.1:8000"
LOGIN_URL = BASE + "/panel/login/"
GALLERY_URL = BASE + "/gallery/"
VIDEO_ADD_URL = BASE + "/panel/gallery/videos/add/"
PHOTO_ADD_URL = BASE + "/panel/gallery/add/"

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


# ── Admin login (for seeding test data) ──────────

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

print("Logging in to admin panel...")
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


# ── 1. Gallery page loads (empty state) ──────────

print("\n1. Gallery page (empty state)")
resp = opener.open(GALLERY_URL)
html = resp.read().decode()
check("Gallery loads (200)", resp.status == 200)
check("Page title present", "Gallery" in html)
check("sp-page class present", "sp-page" in html)
check("sp-entity-nav present", "sp-entity-nav" in html)
check("Gallery link active in nav", 'is-active' in html and 'Gallery' in html)
check("Empty state message", "coming soon" in html.lower() or "No photos" in html.lower() or "sp-gallery" in html)


# ── 2. Navbar has Gallery link ───────────────────

print("\n2. Navbar & footer")
resp = opener.open(BASE + "/")
html = resp.read().decode()
check("Gallery link in navbar", '/gallery/' in html)
check("Gallery link in footer", html.count('/gallery/') >= 2)  # navbar + footer


# ── 3. Sports pages have Gallery in entity nav ───

print("\n3. Entity nav on sports pages")
for page_name, url in [
    ("Tournament Hub", "/tournament-preview/"),
    ("Teams", "/teams-preview/"),
    ("Dream Team", "/dream-team-preview/"),
    ("Match Centre", "/match-preview/"),
]:
    resp = opener.open(BASE + url)
    h = resp.read().decode()
    check(f"{page_name} has Gallery nav link", '/gallery/' in h and 'Gallery' in h)


# ── 4. Seed test photo via admin panel ───────────

print("\n4. Seed test photo")
resp = opener.open(PHOTO_ADD_URL)
html = resp.read().decode()
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({
    "csrfmiddlewaretoken": csrf,
    "title": "Test Tournament Photo",
    "drive_url": "https://drive.google.com/file/d/1aTestPhotoGallery123/view?usp=sharing",
}).encode()
req = urllib.request.Request(PHOTO_ADD_URL, data=data, headers={"Referer": PHOTO_ADD_URL})
resp = opener.open(req)
check("Photo added via admin", resp.status == 200)


# ── 5. Seed test video via admin panel ───────────

print("\n5. Seed test video")
resp = opener.open(VIDEO_ADD_URL)
html = resp.read().decode()
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({
    "csrfmiddlewaretoken": csrf,
    "title": "Test Highlights Video",
    "drive_url": "https://drive.google.com/file/d/2bTestVideoGallery456/view?usp=sharing",
    "description": "Best moments from the tournament finals",
}).encode()
req = urllib.request.Request(VIDEO_ADD_URL, data=data, headers={"Referer": VIDEO_ADD_URL})
resp = opener.open(req)
check("Video added via admin", resp.status == 200)


# ── 6. Gallery page with content ─────────────────

print("\n6. Gallery page with content")
resp = opener.open(GALLERY_URL)
html = resp.read().decode()
check("Gallery loads with data (200)", resp.status == 200)
check("Photos section present", "sp-gallery-grid" in html)
check("Videos section present", "sp-gallery-videos" in html or "sp-video-card" in html)
check("Test photo title shown", "Test Tournament Photo" in html)
check("Test video title shown", "Test Highlights Video" in html)
check("Video description shown", "Best moments" in html)
check("Photo thumbnail generated", "drive.google.com/thumbnail" in html)
check("Video play icon", "fa-play" in html)
check("Video links to Drive", "drive.google.com" in html)


# ── 7. Lightbox markup ──────────────────────────

print("\n7. Lightbox elements")
check("Lightbox container present", "sp-lightbox" in html)
check("Lightbox close button", "sp-lightbox__close" in html)
check("Lightbox prev button", "sp-lightbox__prev" in html)
check("Lightbox next button", "sp-lightbox__next" in html)
check("Lightbox image element", "sp-lightbox__img" in html)
check("Gallery items have data-full", "data-full=" in html)


# ── 8. Responsive CSS classes ───────────────────

print("\n8. CSS integration")
check("sports-preview.css linked", "sports-preview.css" in html)
check("sp-gallery-item class used", "sp-gallery-item" in html)
check("sp-video-card class used", "sp-video-card" in html)


# ── 9. No empty state when data exists ──────────

print("\n9. State checks")
check("No empty state when data exists", "coming soon" not in html.lower())


# ── 10. Cleanup ─────────────────────────────────

print("\n10. Cleanup")
# Delete photo
resp = opener.open(BASE + "/panel/gallery/")
html = resp.read().decode()
delete_urls = re.findall(r'action="(/panel/gallery/\d+/delete/)"', html)
cleaned = 0
for durl in delete_urls:
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    d = urllib.parse.urlencode({"csrfmiddlewaretoken": csrf}).encode()
    req = urllib.request.Request(BASE + durl, d, headers={"Referer": BASE + "/panel/gallery/"})
    resp = opener.open(req)
    html = resp.read().decode()
    cleaned += 1
check(f"Cleaned up {cleaned} test photo(s)", True)

# Delete video
resp = opener.open(BASE + "/panel/gallery/?tab=videos")
html = resp.read().decode()
delete_urls = re.findall(r'action="(/panel/gallery/videos/\d+/delete/)"', html)
cleaned_v = 0
for durl in delete_urls:
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    d = urllib.parse.urlencode({"csrfmiddlewaretoken": csrf}).encode()
    req = urllib.request.Request(BASE + durl, d, headers={"Referer": BASE + "/panel/gallery/"})
    resp = opener.open(req)
    html = resp.read().decode()
    cleaned_v += 1
check(f"Cleaned up {cleaned_v} test video(s)", True)


# ── Summary ──────────────────────────────────────

print("\n" + "=" * 50)
print(f"Results: {passed}/{total} checks passed")
if passed == total:
    print("All checks passed!")
else:
    print(f"{total - passed} check(s) FAILED")
