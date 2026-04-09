"""Stats — inbox (queue-based), per-team CSV import, detail, inline edit."""

import io

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from ..constants import MATCH_FINISHED, POSITION_CHOICES, STAGE_CHOICES, STAGE_GROUP
from ..models import AUDIT_CATEGORY_STATS, Match, Player, PlayerMatchStats, Team, TeamMatchStats
from .audit import log_audit


@staff_member_required(login_url="/panel/login/")
def stats_list_view(request):
    """Stats inbox — matches grouped by import state."""
    matches = list(
        Match.objects.select_related("team_a", "team_b")
        .order_by("-match_number")
    )

    stage_filter = request.GET.get("stage", "")
    if stage_filter:
        matches = [m for m in matches if m.stage == stage_filter]

    # ── Build 4 inbox groups ──
    waiting = []      # FINISHED, no stats
    needs_attn = []   # has partial import (one team only)
    imported = []     # stats_imported == True
    other = []        # not finished yet

    for m in matches:
        if m.stats_imported:
            imported.append(m)
        elif m.status == MATCH_FINISHED:
            # Check if partially imported (one team has data)
            has_a = (
                m.team_a_id
                and PlayerMatchStats.objects.filter(match=m, team=m.team_a).exists()
            )
            has_b = (
                m.team_b_id
                and PlayerMatchStats.objects.filter(match=m, team=m.team_b).exists()
            )
            if has_a or has_b:
                needs_attn.append(m)
            else:
                waiting.append(m)
        else:
            other.append(m)

    groups = [
        {"key": "waiting", "label": "Waiting for CSV", "icon": "fa-hourglass-half",
         "color": "red", "matches": waiting},
        {"key": "needs_attn", "label": "Needs Attention", "icon": "fa-exclamation-circle",
         "color": "yellow", "matches": needs_attn},
        {"key": "imported", "label": "Imported Successfully", "icon": "fa-check-circle",
         "color": "green", "matches": imported},
        {"key": "other", "label": "Not Finished Yet", "icon": "fa-clock",
         "color": "cyan", "matches": other},
    ]

    return render(request, "panel/stats_list.html", {
        "page_title": "Statistics",
        "nav_section": "stats",
        "groups": groups,
        "stage_filter": stage_filter,
        "STAGE_CHOICES": STAGE_CHOICES,
        "total_matches": len(matches),
    })


@staff_member_required(login_url="/panel/login/")
def stats_import_view(request, pk):
    """Two-step CSV stats import: upload → preview → confirm (per-team)."""
    from ..services import confirm_csv_import, preview_csv_import

    match = get_object_or_404(
        Match.objects.select_related("team_a", "team_b"), pk=pk
    )

    preview_rows = None
    errors = []
    warnings = []
    imported_count = None
    selected_team = None

    # Per-team import status
    team_a_imported = (
        match.team_a
        and PlayerMatchStats.objects.filter(match=match, team=match.team_a).exists()
    )
    team_b_imported = (
        match.team_b
        and PlayerMatchStats.objects.filter(match=match, team=match.team_b).exists()
    )

    if request.method == "POST":
        if "confirm" in request.POST:
            # ── Step 2: Confirm import from cached CSV ──
            cached_csv = request.session.pop("_stats_csv_content", None)
            cached_match = request.session.pop("_stats_csv_match", None)
            cached_team = request.session.pop("_stats_csv_team", None)
            if not cached_csv or cached_match != pk:
                messages.error(
                    request, "Session expired. Please upload the file again."
                )
            else:
                try:
                    file_obj = io.StringIO(cached_csv)
                    result = confirm_csv_import(file_obj, pk, cached_team)
                    imported_count = result["imported"]
                    warnings = result.get("warnings", [])
                    if cached_team:
                        selected_team = Team.objects.filter(pk=cached_team).first()
                    # Refresh per-team status after import
                    team_a_imported = (
                        match.team_a
                        and PlayerMatchStats.objects.filter(
                            match=match, team=match.team_a
                        ).exists()
                    )
                    team_b_imported = (
                        match.team_b
                        and PlayerMatchStats.objects.filter(
                            match=match, team=match.team_b
                        ).exists()
                    )
                    team_label = selected_team.name if selected_team else "all"
                    log_audit(
                        user=request.user, category=AUDIT_CATEGORY_STATS,
                        action=f"Stats imported: {imported_count} rows ({team_label})",
                        entity_type="Match", entity_id=match.pk,
                        entity_label=f"M{match.match_number}",
                    )
                    messages.success(
                        request,
                        f"Imported {imported_count} player stats "
                        f"({team_label}) for M{match.match_number}.",
                    )
                except ValueError as exc:
                    errors = [str(exc)]
        else:
            # ── Step 1: Upload + preview ──
            csv_file = request.FILES.get("csv_file")
            team_id_str = request.POST.get("team_id", "")
            if not csv_file:
                messages.error(request, "Please select a CSV file.")
            elif not team_id_str:
                messages.error(request, "Please select a team.")
            else:
                try:
                    team_id = int(team_id_str)
                except (ValueError, TypeError):
                    team_id = None
                if team_id is None:
                    messages.error(request, "Invalid team selection.")
                else:
                    selected_team = Team.objects.filter(pk=team_id).first()
                    raw = csv_file.read()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8-sig")
                    csv_file.seek(0)

                    result = preview_csv_import(csv_file, pk, team_id)
                    errors = result["errors"]
                    warnings = result["warnings"]

                    if result["can_import"]:
                        preview_rows = result["preview"]
                        # Cache raw CSV text in session for confirm step
                        request.session["_stats_csv_content"] = raw
                        request.session["_stats_csv_match"] = pk
                        request.session["_stats_csv_team"] = team_id

    # ── Import diff summary (for confirmation screen) ──
    import_diff = None
    if preview_rows and selected_team:
        existing_count = PlayerMatchStats.objects.filter(
            match=match, team=selected_team,
        ).count()
        both_teams_done = team_a_imported and team_b_imported
        will_complete = (
            not match.stats_imported
            and (both_teams_done or (not team_a_imported and not team_b_imported))
        )
        # Check if this import will make the other team complete too
        other_team_has = False
        if selected_team == match.team_a and team_b_imported:
            other_team_has = True
        elif selected_team == match.team_b and team_a_imported:
            other_team_has = True
        will_finish = other_team_has and not match.stats_imported
        import_diff = {
            "new_rows": len(preview_rows),
            "replacing": existing_count,
            "is_reimport": existing_count > 0,
            "will_recalc_standings": match.stage == STAGE_GROUP and will_finish,
            "will_refresh_dreamteam": True,
            "will_mark_imported": will_finish,
        }

    return render(request, "panel/stats_import.html", {
        "page_title": f"Import Stats — M{match.match_number}",
        "nav_section": "stats",
        "match": match,
        "preview_rows": preview_rows,
        "errors": errors,
        "warnings": warnings,
        "imported_count": imported_count,
        "selected_team": selected_team,
        "team_a_imported": team_a_imported,
        "team_b_imported": team_b_imported,
        "import_diff": import_diff,
    })


@staff_member_required(login_url="/panel/login/")
def stats_detail_view(request, pk):
    """View imported stats for a match, grouped by team."""
    match = get_object_or_404(
        Match.objects.select_related("team_a", "team_b"), pk=pk
    )
    stats_a = (
        PlayerMatchStats.objects.filter(match=match, team=match.team_a)
        .select_related("player")
        .order_by("jersey_number")
        if match.team_a
        else []
    )
    stats_b = (
        PlayerMatchStats.objects.filter(match=match, team=match.team_b)
        .select_related("player")
        .order_by("jersey_number")
        if match.team_b
        else []
    )
    team_stats_a = (
        TeamMatchStats.objects.filter(match=match, team=match.team_a).first()
        if match.team_a
        else None
    )
    team_stats_b = (
        TeamMatchStats.objects.filter(match=match, team=match.team_b).first()
        if match.team_b
        else None
    )

    return render(request, "panel/stats_detail.html", {
        "page_title": f"Stats — M{match.match_number}",
        "nav_section": "stats",
        "match": match,
        "stats_a": stats_a,
        "stats_b": stats_b,
        "team_stats_a": team_stats_a,
        "team_stats_b": team_stats_b,
    })


# Editable stat fields in order
_STAT_FIELDS = [
    "serve_attempts", "aces", "serve_errors",
    "attack_attempts", "kills", "attack_errors",
    "pass_attempts", "perfect_passes", "pass_errors",
    "blocks", "assists", "setting_errors",
]


@staff_member_required(login_url="/panel/login/")
def stats_edit_view(request, pk):
    """Inline-edit player stats for a match, then recalculate aggregates."""
    from ..services import (
        _aggregate_team_stats,
        recalculate_dream_team,
        recalculate_standings,
    )

    match = get_object_or_404(
        Match.objects.select_related("team_a", "team_b"), pk=pk
    )
    player_stats = (
        PlayerMatchStats.objects.filter(match=match)
        .select_related("player", "team")
        .order_by("team__name", "jersey_number")
    )

    if request.method == "POST":
        errors = []
        for ps in player_stats:
            for field in _STAT_FIELDS:
                key = f"stat_{ps.pk}_{field}"
                val = request.POST.get(key, "").strip()
                if val == "":
                    val = 0
                try:
                    int_val = int(val)
                    if int_val < 0:
                        raise ValueError
                except (ValueError, TypeError):
                    errors.append(
                        f"{ps.player} — {field}: invalid value '{request.POST.get(key, '')}'."
                    )
                    continue
                setattr(ps, field, int_val)

            # Position
            pos_key = f"stat_{ps.pk}_position"
            pos_val = request.POST.get(pos_key, ps.position).strip().upper()
            ps.position = pos_val

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            # Save all
            for ps in player_stats:
                ps.save()

            # Recalculate team aggregates
            TeamMatchStats.objects.filter(match=match).delete()
            _aggregate_team_stats(match)

            # Recalculate standings / dream team
            if match.stage == STAGE_GROUP:
                recalculate_standings()
            recalculate_dream_team()

            messages.success(
                request,
                f"Stats updated for M{match.match_number}. Aggregates recalculated.",
            )
            return redirect("panel:stats_detail", pk=pk)

    # ── Group stats by team for separated display ──
    stats_team_a = [ps for ps in player_stats if ps.team_id == match.team_a_id]
    stats_team_b = [ps for ps in player_stats if ps.team_id == match.team_b_id]

    # ── Compute column totals per team ──
    def _team_totals(rows):
        totals = {f: 0 for f in _STAT_FIELDS}
        for ps in rows:
            for f in _STAT_FIELDS:
                totals[f] += getattr(ps, f, 0)
        return totals

    totals_a = _team_totals(stats_team_a) if stats_team_a else None
    totals_b = _team_totals(stats_team_b) if stats_team_b else None

    return render(request, "panel/stats_edit.html", {
        "page_title": f"Edit Stats — M{match.match_number}",
        "nav_section": "stats",
        "match": match,
        "player_stats": player_stats,
        "stats_team_a": stats_team_a,
        "stats_team_b": stats_team_b,
        "totals_a": totals_a,
        "totals_b": totals_b,
        "STAT_FIELDS": _STAT_FIELDS,
        "POSITION_CHOICES": POSITION_CHOICES,
    })
