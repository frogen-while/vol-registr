# Pocket Aces Tournament Platform — Archived Implementation Plan

> Archived on 2026-05-02 during repository cleanup.
> This file used to describe a mock-to-database migration for a preview-page stack that is no longer part of the live application.

---

## Current Status

- The old preview-page surface described here has been removed from the repo and is no longer a valid implementation target.
- `tournament/sports_data.py` has been deleted because it had no live call sites.
- The following preview templates/routes/assets referenced by the old plan are gone and should not be used for new work:
  - `tournament/templates/tournament/tournament_preview.html`
  - `tournament/templates/tournament/teams_preview.html`
  - `tournament/templates/tournament/dream_team_preview.html`
  - `tournament/templates/tournament/match_preview.html`
  - `tournament/templates/tournament/team_preview.html`
  - `tournament/templates/tournament/player_preview.html`
  - `tournament/templates/tournament/partials/preview_nav.html`
  - `static/js/sports-preview.js`
  - `static/css/sports-preview.css`

## Live Public Surface

Use the current registration-first public pages instead of the archived preview stack:

- `tournament/views.py`
  - `index`
  - `tournament_hub`
  - `tournament_gallery`
  - `faq`
  - `roster_update_view`
  - registration and voting endpoints
- `tournament/templates/tournament/`
  - `index.html`
  - `register.html`
  - `gallery.html`
  - `faq.html`
  - `match_coming_soon.html`
  - `roster_update.html`
  - `team_detail.html`

## Active Docs To Use Instead

- `docs/public-entity-pages-redesign-phases.md` for current public-site redesign work
- `docs/admin-panel-redesign-blueprint.md` for admin-panel structure and UX
- `docs/admin-panel-redesign-phases.md` for phased panel implementation work
- `docs/match-page-technical-spec.md` and `docs/match-page-issue-list.md` if Match Centre work is restarted
- `docs/minimal-tournament-stats-model.md` for a smaller stats-model reintroduction path

## If Match Centre Returns Later

Do not revive this document as-is. Start a fresh spec from the current codebase state:

1. Define the new public routes and templates around the live site, not around deleted preview routes.
2. Re-introduce stats models/services only when they have real runtime consumers.
3. Plan migrations from the current `tournament` app state; migration debt still exists and must be handled separately.
4. Prefer smaller, verifiable increments over a large mock-preview architecture.

## Why This File Was Archived

The original plan assumed:

- six mock sports preview pages would stay in the repository
- `sports-preview.js` and `sports-preview.css` were active assets
- a dedicated `sports_data.py` service layer would back those pages

Those assumptions are no longer true after the May 2026 cleanup, so keeping the old step-by-step plan in active form created stale references and misleading implementation guidance.