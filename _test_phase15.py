"""Smoke tests for Phase 15 — Dream Team Management."""
import re
import urllib.request
import urllib.parse

BASE = "http://127.0.0.1:8000"
LOGIN_URL = BASE + "/panel/login/"
DT_URL = BASE + "/panel/dreamteam/"
DT_AUTOFILL_URL = BASE + "/panel/dreamteam/autofill/"
DT_RESET_URL = BASE + "/panel/dreamteam/reset/"

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


# ── 1. Dream Team page loads ───────────────────────────

print("\n1. Dream Team page")
resp = opener.open(DT_URL)
html = resp.read().decode()
check("Page loads (200)", resp.status == 200)
check("Court layout present", "pnl-dt-court" in html)
check("Front-left slot", 'data-slot="front-left"' in html)
check("Front-center slot", 'data-slot="front-center"' in html)
check("Front-right slot", 'data-slot="front-right"' in html)
check("Back-left slot", 'data-slot="back-left"' in html)
check("Back-center slot", 'data-slot="back-center"' in html)
check("Back-right slot", 'data-slot="back-right"' in html)
check("Libero slot", 'data-slot="libero"' in html)
check("Auto-fill button", "Auto-fill" in html)
check("Save button", "Save Dream Team" in html)


# ── 2. Auto-fill (POST) ───────────────────────────────

print("\n2. Auto-fill")
resp2 = opener.open(DT_URL)
html2 = resp2.read().decode()
csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html2).group(1)
data2 = urllib.parse.urlencode({"csrfmiddlewaretoken": csrf2}).encode()
req2 = urllib.request.Request(DT_AUTOFILL_URL, data=data2, headers={"Referer": DT_URL})
resp2 = opener.open(req2)
final_url = resp2.geturl()
check("Auto-fill redirects to dreamteam", "/panel/dreamteam" in final_url)
html2 = resp2.read().decode()
check("Success message shown", "auto-filled" in html2.lower() or "Auto-filled" in html2)


# ── 3. Reset (POST) ───────────────────────────────────

print("\n3. Reset")
resp3 = opener.open(DT_URL)
html3 = resp3.read().decode()
csrf3 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html3).group(1)
data3 = urllib.parse.urlencode({"csrfmiddlewaretoken": csrf3}).encode()
req3 = urllib.request.Request(DT_RESET_URL, data=data3, headers={"Referer": DT_URL})
resp3 = opener.open(req3)
check("Reset redirects", "/panel/dreamteam" in resp3.geturl())
html3 = resp3.read().decode()
check("Reset message", "cleared" in html3.lower() or "Clear" in html3)


# ── 4. Manual save (POST empty → no entries) ──────────

print("\n4. Manual save (empty)")
resp4 = opener.open(DT_URL)
html4 = resp4.read().decode()
csrf4 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html4).group(1)
data4 = urllib.parse.urlencode({"csrfmiddlewaretoken": csrf4}).encode()
req4 = urllib.request.Request(DT_URL, data=data4, headers={"Referer": DT_URL})
resp4 = opener.open(req4)
check("Save returns 200", resp4.status == 200)
html4 = resp4.read().decode()
check("Saved message", "saved" in html4.lower() or "Dream Team saved" in html4)


# ── Summary ────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"Phase 15 Results: {passed}/{total} passed")
if passed == total:
    print("ALL TESTS PASSED")
else:
    print(f"FAILURES: {total - passed}")
