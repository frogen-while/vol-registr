"""Audit timeline — global filterable event log + command palette search."""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from ..models import AUDIT_CATEGORY_CHOICES, AuditEntry, Match, Team


@staff_member_required(login_url="/panel/login/")
def audit_view(request):
    """Global audit timeline with category and entity filters."""
    qs = AuditEntry.objects.select_related("user").order_by("-timestamp")

    category = request.GET.get("category", "")
    if category:
        qs = qs.filter(category=category)

    entity = request.GET.get("entity", "")
    if entity:
        qs = qs.filter(entity_type=entity)

    entries = qs[:200]

    return render(request, "panel/audit.html", {
        "page_title": "Audit Timeline",
        "nav_section": "audit",
        "entries": entries,
        "category_choices": AUDIT_CATEGORY_CHOICES,
        "current_category": category,
        "current_entity": entity,
    })


# ── Command Palette search endpoint ─────────────────────
_PAGES = [
    {"label": "Control Room", "icon": "fa-tower-broadcast", "type": "page"},
    {"label": "Teams", "icon": "fa-users", "type": "page"},
    {"label": "Players", "icon": "fa-user", "type": "page"},
    {"label": "Pipeline", "icon": "fa-columns", "type": "page"},
    {"label": "Check-in Desk", "icon": "fa-clipboard-check", "type": "page"},
    {"label": "Schedule", "icon": "fa-calendar-alt", "type": "page"},
    {"label": "Statistics", "icon": "fa-chart-bar", "type": "page"},
    {"label": "Rankings", "icon": "fa-trophy", "type": "page"},
    {"label": "Gallery", "icon": "fa-images", "type": "page"},
    {"label": "Audit Log", "icon": "fa-clock-rotate-left", "type": "page"},
]

_PAGE_URLS = {
    "Control Room": "panel:dashboard",
    "Teams": "panel:teams",
    "Players": "panel:players",
    "Pipeline": "panel:teams_pipeline",
    "Check-in Desk": "panel:checkin",
    "Schedule": "panel:schedule",
    "Statistics": "panel:stats",
    "Rankings": "panel:rankings",
    "Gallery": "panel:gallery",
    "Audit Log": "panel:audit",
}


@staff_member_required(login_url="/panel/login/")
def cmd_search(request):
    """Return JSON results for the command palette fuzzy search."""
    q = request.GET.get("q", "").strip().lower()
    results = []

    if not q:
        # Return pages as default suggestions
        for p in _PAGES:
            results.append({
                "label": p["label"],
                "icon": p["icon"],
                "type": p["type"],
                "url": reverse(_PAGE_URLS[p["label"]]),
            })
        return JsonResponse({"results": results[:15]})

    # Pages
    for p in _PAGES:
        if q in p["label"].lower():
            results.append({
                "label": p["label"],
                "icon": p["icon"],
                "type": "page",
                "url": reverse(_PAGE_URLS[p["label"]]),
            })

    # Teams
    teams = Team.objects.filter(name__icontains=q)[:8]
    for t in teams:
        results.append({
            "label": t.name,
            "icon": "fa-users",
            "type": "team",
            "url": reverse("panel:team_detail", args=[t.pk]),
        })

    # Matches
    matches = Match.objects.select_related("team_a", "team_b").filter(
        models_Q_match_search(q)
    )[:8]
    for m in matches:
        label = f"M{m.match_number}: {m.team_a or 'TBD'} vs {m.team_b or 'TBD'}"
        results.append({
            "label": label,
            "icon": "fa-calendar-alt",
            "type": "match",
            "url": reverse("panel:match_edit", args=[m.pk]),
        })

    return JsonResponse({"results": results[:15]})


def models_Q_match_search(q):
    """Build a Q filter for matches matching the query string."""
    from django.db.models import Q
    filters = Q(team_a__name__icontains=q) | Q(team_b__name__icontains=q)
    # Also try match number
    if q.lstrip("m").isdigit():
        filters |= Q(match_number=int(q.lstrip("m")))
    return filters
