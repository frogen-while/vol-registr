"""Dream Team — 7-slot court layout, auto-fill preview, override markers."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..constants import (
    MVP_WEIGHTS,
    POSITION_L,
    POSITION_MB,
    POSITION_OH,
    POSITION_OPP,
    POSITION_S,
)
from ..models import AUDIT_CATEGORY_DREAMTEAM, DreamTeamEntry, Player, PlayerMatchStats
from .audit import log_audit

SLOTS = [
    ("front-left", "OH", "Outside Hitter"),
    ("front-center", "MB", "Middle Blocker"),
    ("front-right", "OPP", "Opposite"),
    ("back-left", "S", "Setter"),
    ("back-center", "MB", "Middle Blocker"),
    ("back-right", "OH", "Outside Hitter"),
    ("libero", "L", "Libero"),
]

_SLOT_MAP = {
    POSITION_OH: ["front-left", "back-right"],
    POSITION_MB: ["front-center", "back-center"],
    POSITION_OPP: ["front-right"],
    POSITION_S: ["back-left"],
    POSITION_L: ["libero"],
}


def _build_candidates(top_n=5):
    """Return {position: [{player_id, name, team, jersey, score, sets, metric}, ...]}.

    Uses weighted per-set MVP formulas from MVP_WEIGHTS.
    """
    candidates: dict[str, list] = {}
    for pos, weights in MVP_WEIGHTS.items():
        agg_fields = list({f for f, _ in weights}) + ["sets_played"]
        agg_kwargs = {f: Sum(f) for f in agg_fields}
        rows = list(
            PlayerMatchStats.objects.filter(position=pos)
            .values(
                "player_id",
                "player__first_name",
                "player__last_name",
                "player__jersey_number",
                "team__name",
            )
            .annotate(**agg_kwargs)
        )

        scored: list[tuple[float, int, dict]] = []
        for r in rows:
            total_sets = r.get("sets_played") or 0
            if total_sets == 0:
                continue
            # "Did they play?" filter
            if pos == POSITION_S:
                if (r.get("assists") or 0) == 0 and (r.get("setting_errors") or 0) == 0:
                    continue
            elif pos == POSITION_L:
                if (r.get("pass_errors") or 0) == 0:
                    continue
            else:
                if all((r.get(f) or 0) == 0 for f, _ in weights):
                    continue

            raw_score = sum(
                (r.get(field) or 0) * weight for field, weight in weights
            )
            per_set = raw_score / total_sets
            scored.append((per_set, total_sets, r))

        # L: closest to 0; others: descending
        if pos == POSITION_L:
            scored.sort(key=lambda x: abs(x[0]))
        else:
            scored.sort(key=lambda x: x[0], reverse=True)

        candidates[pos] = [
            {
                "player_id": r["player_id"],
                "name": f'{r["player__last_name"]} {r["player__first_name"]}',
                "jersey": r["player__jersey_number"],
                "team": r["team__name"],
                "score": round(per_set, 2),
                "sets": total_sets,
                "metric": f"{per_set:+.2f}/set",
            }
            for per_set, total_sets, r in scored[:top_n]
        ]
    return candidates


def _compute_autofill_preview(current_entries):
    """Compute what auto-fill WOULD produce vs current state.

    Returns list of dicts: {slot_id, position, label, current_player, new_player, changed}.
    """
    candidates = _build_candidates(top_n=10)
    preview = []
    for pos, slots in _SLOT_MAP.items():
        pos_candidates = candidates.get(pos, [])
        for i, slot_id in enumerate(slots):
            slot_label = next((lbl for sid, _p, lbl in SLOTS if sid == slot_id), "")
            current = current_entries.get(slot_id)
            new_candidate = pos_candidates[i] if i < len(pos_candidates) else None
            preview.append({
                "slot_id": slot_id,
                "position": pos,
                "label": slot_label,
                "current_player": (
                    f"#{current.player.jersey_number} {current.player.last_name} {current.player.first_name}"
                    if current and current.player else None
                ),
                "current_player_id": current.player_id if current else None,
                "current_is_auto": current.is_auto if current else None,
                "new_player": (
                    f"#{new_candidate['jersey']} {new_candidate['name']}"
                    if new_candidate else None
                ),
                "new_player_id": new_candidate["player_id"] if new_candidate else None,
                "new_metric": (
                    new_candidate["metric"]
                    if new_candidate else None
                ),
                "changed": (
                    (current.player_id if current else None) !=
                    (new_candidate["player_id"] if new_candidate else None)
                ),
            })
    return preview


@staff_member_required(login_url="/panel/login/")
def dreamteam_view(request):
    """Display / manually edit the Dream Team 7-slot court with candidates."""

    if request.method == "POST":
        DreamTeamEntry.objects.all().delete()
        entries = []
        for slot_id, default_pos, _label in SLOTS:
            player_id = request.POST.get(f"player_{slot_id}")
            if not player_id:
                continue
            player = Player.objects.filter(pk=player_id).select_related("team").first()
            if not player:
                continue
            metric_label = request.POST.get(f"metric_label_{slot_id}", "")
            metric_value = request.POST.get(f"metric_value_{slot_id}", "0")
            try:
                metric_value = float(metric_value)
            except (ValueError, TypeError):
                metric_value = 0
            entries.append(
                DreamTeamEntry(
                    position=default_pos,
                    slot=slot_id,
                    player=player,
                    team=player.team,
                    metric_label=metric_label,
                    metric_value=metric_value,
                    is_auto=False,
                )
            )
        DreamTeamEntry.objects.bulk_create(entries)
        messages.success(request, f"Dream Team saved ({len(entries)} slots).")
        return redirect("panel:dreamteam")

    # Build current entries keyed by slot
    current = {e.slot: e for e in DreamTeamEntry.objects.select_related("player", "team").all()}
    players = Player.objects.select_related("team").order_by("team__name", "last_name", "first_name")

    # Candidates per position (top-5)
    candidates = _build_candidates(top_n=5)

    # Publish readiness
    filled_count = len(current)
    total_slots = len(SLOTS)
    empty_count = total_slots - filled_count
    publish_ready = filled_count == total_slots

    slots_data = []
    for slot_id, default_pos, label in SLOTS:
        entry = current.get(slot_id)
        slots_data.append({
            "slot_id": slot_id,
            "position": default_pos,
            "label": label,
            "entry": entry,
            "is_auto": entry.is_auto if entry else None,
            "candidates": candidates.get(default_pos, []),
        })

    # Unique position groups for candidate tables
    position_groups = []
    seen_positions = set()
    _pos_labels = {p: l for _, p, l in SLOTS}
    for pos in [POSITION_OH, POSITION_MB, POSITION_OPP, POSITION_S, POSITION_L]:
        if pos not in seen_positions:
            seen_positions.add(pos)
            cands = candidates.get(pos, [])
            if cands:
                position_groups.append({
                    "position": pos,
                    "label": _pos_labels.get(pos, pos),
                    "candidates": cands,
                })

    return render(request, "panel/dreamteam.html", {
        "page_title": "Dream Team",
        "nav_section": "dreamteam",
        "slots": slots_data,
        "players": players,
        "has_entries": bool(current),
        "filled_count": filled_count,
        "total_slots": total_slots,
        "empty_count": empty_count,
        "publish_ready": publish_ready,
        "position_groups": position_groups,
    })


@staff_member_required(login_url="/panel/login/")
def dreamteam_preview_view(request):
    """Show what auto-fill would change BEFORE applying."""
    current = {e.slot: e for e in DreamTeamEntry.objects.select_related("player", "team").all()}
    preview = _compute_autofill_preview(current)
    changes_count = sum(1 for p in preview if p["changed"])

    return render(request, "panel/dreamteam_preview.html", {
        "page_title": "Auto-fill Preview",
        "nav_section": "dreamteam",
        "preview": preview,
        "changes_count": changes_count,
        "has_entries": bool(current),
    })


@staff_member_required(login_url="/panel/login/")
@require_POST
def dreamteam_autofill_view(request):
    """Recalculate dream team from stats (auto-fill)."""
    from ..services import recalculate_dream_team

    recalculate_dream_team()
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_DREAMTEAM,
        action="Dream Team auto-filled from stats",
    )
    messages.success(request, "Dream Team auto-filled from player stats.")
    return redirect("panel:dreamteam")


@staff_member_required(login_url="/panel/login/")
@require_POST
def dreamteam_reset_view(request):
    """Delete all Dream Team entries."""
    deleted, _ = DreamTeamEntry.objects.all().delete()
    log_audit(
        user=request.user, category=AUDIT_CATEGORY_DREAMTEAM,
        action=f"Dream Team cleared ({deleted} entries)",
    )
    messages.success(request, f"Dream Team cleared ({deleted} entries removed).")
    return redirect("panel:dreamteam")
