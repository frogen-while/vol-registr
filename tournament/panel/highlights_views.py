"""Highlights — CRUD for MatchHighlight, feature toggle."""

import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..admin_forms import MatchHighlightForm
from ..models import AUDIT_CATEGORY_MEDIA, Match, MatchHighlight
from .audit import log_audit


@staff_member_required(login_url="/panel/login/")
def highlights_list_view(request):
    """List all highlights, filterable by match and featured status."""
    qs = MatchHighlight.objects.select_related("match").order_by("order")
    match_filter = request.GET.get("match")
    if match_filter:
        qs = qs.filter(match_id=match_filter)
    featured_filter = request.GET.get("featured")
    if featured_filter == "1":
        qs = qs.filter(is_featured=True)

    matches = Match.objects.order_by("match_number")

    return render(request, "panel/highlights.html", {
        "page_title": "Highlights",
        "nav_section": "highlights",
        "highlights": qs,
        "matches": matches,
        "current_match": match_filter,
        "current_featured": featured_filter,
    })


@staff_member_required(login_url="/panel/login/")
def highlight_add_view(request):
    """Add a new highlight."""
    form = MatchHighlightForm()
    if request.method == "POST":
        form = MatchHighlightForm(request.POST)
        if form.is_valid():
            hl = form.save(commit=False)
            if not hl.order:
                max_order = MatchHighlight.objects.aggregate(m=Max("order"))["m"] or 0
                hl.order = max_order + 1
            hl.save()
            messages.success(request, f'Highlight "{hl.title}" added.')
            return redirect("panel:highlights")
    return render(request, "panel/highlight_form.html", {
        "page_title": "Add Highlight",
        "nav_section": "highlights",
        "form": form,
    })


@staff_member_required(login_url="/panel/login/")
def highlight_edit_view(request, pk):
    """Edit an existing highlight."""
    hl = get_object_or_404(MatchHighlight, pk=pk)
    form = MatchHighlightForm(instance=hl)
    if request.method == "POST":
        form = MatchHighlightForm(request.POST, instance=hl)
        if form.is_valid():
            form.save()
            messages.success(request, f'Highlight "{hl.title}" updated.')
            return redirect("panel:highlights")
    return render(request, "panel/highlight_form.html", {
        "page_title": "Edit Highlight",
        "nav_section": "highlights",
        "form": form,
        "highlight": hl,
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def highlight_delete_view(request, pk):
    """Delete a highlight."""
    hl = get_object_or_404(MatchHighlight, pk=pk)
    hl.delete()
    messages.success(request, "Highlight deleted.")
    return redirect("panel:highlights")


@staff_member_required(login_url="/panel/login/")
@require_POST
def highlight_toggle_featured_view(request, pk):
    """Toggle featured status on a highlight."""
    hl = get_object_or_404(MatchHighlight, pk=pk)
    hl.is_featured = not hl.is_featured
    hl.save(update_fields=["is_featured"])
    status = "featured" if hl.is_featured else "unfeatured"
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_MEDIA,
        action=f"Highlight {status}: {hl.title}",
        entity_type="MatchHighlight", entity_id=hl.pk, entity_label=hl.title,
    )
    messages.success(request, f'Highlight "{hl.title}" {status}.')
    return redirect("panel:highlights")


@staff_member_required(login_url="/panel/login/")
@require_POST
def highlight_reorder_view(request):
    """AJAX endpoint — receives JSON array of highlight IDs in new order."""
    try:
        order_ids = json.loads(request.body)
        if not isinstance(order_ids, list):
            return JsonResponse({"error": "Expected a list"}, status=400)
        for idx, hl_id in enumerate(order_ids):
            MatchHighlight.objects.filter(pk=hl_id).update(order=idx)
        return JsonResponse({"ok": True})
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)
