# Pocket Aces Tournament - admin panel redesign blueprint

## 1. Objective

This document defines the target shape of the custom tournament admin panel.

The goal is not to produce a prettier CRUD layer. The goal is to turn the existing panel into a fast operational system for tournament staff.

The redesigned panel must help staff do five things with less friction:

- process registrations faster
- control match-day operations in one place
- import and validate statistics with fewer mistakes
- publish media and editorial selections without context switching
- reduce the number of full-page transitions during live work

---

## 2. Current state diagnosis

The current panel already covers important business flows:

- dashboard
- teams
- check-in
- schedule
- stats import and edit
- gallery
- Dream Team

This is good because the product is already operationally useful.

The problem is that the interface still behaves like a set of separate admin pages instead of one tournament control system.

The main bottlenecks are:

### 2.1 Navigation overhead

Operators jump between list pages, detail pages, edit pages and import pages too often.

Result:

- loss of context
- slower repetitive work
- more chances to forget the previous item state

### 2.2 Table-first interaction model

The current panel is effective for raw listing, but not for rapid operational action.

Tables are useful for scanning many records.
Tables are weak as the only interaction pattern for live tournament work.

### 2.3 Mixed workflow density

The same panel serves different roles:

- registration staff
- check-in desk
- schedule coordinator
- stats operator
- media editor
- tournament lead

These roles need different home screens, different priorities and different shortcuts.

### 2.4 Large server-side monolith

The custom admin logic is already substantial and concentrated in one large view module.

That makes future UI improvements harder because every new workflow risks increasing coupling between unrelated features.

### 2.5 Missing operational surfaces

The panel has data management screens, but it does not yet have strong operational surfaces such as:

- command center dashboard
- queue-based worklists
- conflict review surfaces
- reconciliation screens
- role-specific quick actions
- audit-oriented event timeline

---

## 3. Product definition

The redesigned panel should behave like a tournament operating system.

That means:

- one place to see what needs attention now
- one place to process registrations and team readiness
- one place to control courts, timeslots and match status
- one place to import, validate and repair stats
- one place to prepare media and editorial outputs

The panel should feel closer to a newsroom plus operations desk than to a generic admin dashboard.

---

## 4. Design principles

### 4.1 Action before reporting

Every key page must answer:

- what is waiting
- what is blocked
- what can be completed in one interaction

### 4.2 Context without page churn

Details should open in drawers, side panels, stacked overlays or inline expansion when possible.

Full-page navigation should be reserved for:

- large forms
- deep review flows
- complex conflict resolution

### 4.3 Role-aware hierarchy

The first screen for each role must show the work queue most relevant to that role.

### 4.4 State visibility

Every entity must show its operational state clearly.

Examples:

- team readiness
- payment completeness
- roster completeness
- stats import completeness
- publishing completeness

### 4.5 Bulk work is a first-class feature

Tournament staff should not need to repeat the same action record by record when the system can support controlled multi-select actions.

### 4.6 Fast read, dense layout

The panel should be information-dense but not visually noisy.

The target feel is:

- compact
- precise
- high-contrast
- operational

---

## 5. Target information architecture

The current navigation can be consolidated into five top-level zones.

### 5.1 Control Room

Purpose:
single operational overview for the tournament lead and any staff member starting a shift.

Includes:

- critical alerts
- next two hours timeline
- pending queues
- active matches
- unresolved data issues
- media and publishing tasks

### 5.2 Teams and Registration

Purpose:
all pre-match team readiness workflows.

Includes:

- registration review
- payment workflow
- roster completion
- contact quality
- group assignment
- roster access code management
- team notes

### 5.3 Match Operations

Purpose:
control schedule, courts and live match state.

Includes:

- court board
- list schedule
- match status updates
- timeslot management
- conflict detection
- match quick actions

### 5.4 Stats and Rankings

Purpose:
process statistics from import to validation to recalculated outputs.

Includes:

- import inbox
- preview and reconciliation
- mismatch repair
- stats edit mode
- standings refresh
- leaderboards
- Dream Team candidate logic

### 5.5 Media and Publishing

Purpose:
prepare public-facing content derived from tournament operations.

Includes:

- gallery intake
- media tagging
- match or team linking
- featured highlights
- Dream Team publishing support
- publish readiness

---

## 6. Roles and tailored home states

### 6.1 Tournament Director

Needs:

- critical issues now
- active courts
- missing stats
- teams not ready
- pending editorial approvals

Home state:
Control Room with alerts, live board and cross-module queues.

### 6.2 Registration Manager

Needs:

- teams by registration state
- payment follow-up
- roster completeness
- captain contact completeness

Home state:
Teams and Registration pipeline.

### 6.3 Check-in Operator

Needs:

- fast lookup
- approved team list
- arrival status
- missing payment or roster warnings

Home state:
Check-in desk mode.

### 6.4 Schedule Coordinator

Needs:

- court board
- time conflicts
- quick match edits
- downstream impact of schedule changes

Home state:
Match Operations board.

### 6.5 Stats Operator

Needs:

- matches waiting for CSV
- preview queues
- import errors
- unmatched players
- recalculation confirmation

Home state:
Stats inbox.

### 6.6 Media Editor

Needs:

- new uploads
- missing tags
- unlinked content
- featured candidates

Home state:
Media intake board.

---

## 7. Core screen concepts

## 7.1 Control Room

This replaces the dashboard as a static KPI page.

It should be built as a decision screen.

### Layout

- top alert rail
- left main queue column
- center live timeline or active court board
- right side intelligence column

### Top alert rail

Shows urgent issues only, for example:

- approved teams not checked in
- matches starting soon without assigned teams
- finished matches without imported stats
- stats imports with unmatched players
- gallery items without tags

### Main queue column

Cards grouped by urgency:

- critical now
- next up
- blocked items
- waiting review

Each queue card should have a direct action button.

Examples:

- review 3 unpaid approved teams
- import stats for match 17
- resolve conflict on Court 2 at 15:30

### Live timeline

Shows the next two hours in a dense operational format:

- current time marker
- upcoming matches
- live matches
- delayed matches
- courts with no assignment

### Intelligence column

Compact operational summaries:

- check-in progress
- stats completion rate
- top scoring match of the day
- latest audit entries
- new media awaiting tag

---

## 7.2 Teams and Registration workspace

This module should support two primary modes.

### Mode A: pipeline board

Columns:

- Registered
- Awaiting Payment
- Paid
- Approved
- Checked-in

Each team card shows:

- team name
- captain name
- group
- player count
- readiness badges
- last activity timestamp

Readiness badges should include:

- payment verified
- roster complete
- no duplicate jersey numbers
- logo uploaded
- captain contacts complete

This board is the fastest way to process the flow of registrations.

### Mode B: dense table

Used for:

- sorting
- filtering
- bulk actions
- large batch review

The table should support saved views:

- all unpaid teams
- approved but no roster code
- approved but not checked in
- incomplete captain contacts
- suspicious roster issues

### Team drawer

Clicking a team should open a right-side drawer instead of forcing a full-page jump.

The drawer includes:

- identity header
- operational status rail
- captain contacts
- payment state
- roster status
- roster code controls
- internal staff notes
- match summary
- audit timeline

Primary quick actions in the drawer:

- change status
- mark payment verified
- generate or regenerate roster code
- assign group
- open full roster editor
- flag for follow-up

### Full team workspace

Still needed for advanced edits.

Use this only for:

- complete team editing
- roster inline editing
- historical review
- internal notes and attachments

---

## 7.3 Check-in desk mode

This should be optimized for event-day speed.

### Core requirements

- instant team search
- large touch-friendly controls
- status visible from distance
- no deep navigation

### Main surface

- large search field
- queue of approved teams not yet checked in
- checked-in counter
- warning groups for incomplete teams

### Team arrival card

When a team is selected, show a large card with:

- team name
- captain name
- group
- roster completeness
- payment state
- current issues

Primary actions:

- mark checked in
- mark issue resolved
- add arrival note
- send to coordinator

### Secondary logic

Check-in should not be only a boolean toggle.

It should allow structured arrival states:

- arrived complete
- arrived with payment issue
- arrived with roster issue
- waiting coordinator

Even if the database keeps a final checked-in flag, the UI should support richer operational notes.

---

## 7.4 Match Operations workspace

This module should become the central logistics desk.

### Primary mode: court board

Grid model:

- columns are courts
- rows are timeslots
- cards are matches

Each match card shows:

- match number
- stage
- teams
- status
- current score if live or finished
- stats imported indicator

### Match quick panel

Selecting a match opens a side panel with:

- status controls
- time and court
- teams
- score
- open stats import
- open stats detail
- attach highlight flag
- jump to team pages

### Conflict system

When moving or editing a match, the panel should show warnings such as:

- court already occupied
- same team double-booked
- empty team assignment
- stage inconsistency
- knock-on shift risk for later matches

### Secondary mode: schedule table

Retain a dense table for:

- admin review
- filters
- CSV import
- audit comparison

### Secondary mode: bracket rail

For knockout stages, add a bracket-first view that helps staff understand progression and publication readiness.

---

## 7.5 Stats and Rankings workspace

This is where the biggest operational upgrade should happen.

The current system already imports, previews and edits stats.
The redesign should turn this into a queue-driven flow.

### Stats inbox

Primary list of matches grouped by state:

- waiting for upload
- preview ready
- needs reconciliation
- imported successfully
- manually edited after import

### Reconciliation screen

After a CSV preview, the operator should see:

- left panel: parsed CSV rows
- center panel: matched players
- right panel: warnings and unresolved issues

Example issue types:

- unmatched jersey number
- duplicate player candidate
- suspicious position
- extreme metric anomaly

### Confirmation diff

Before final import, show the operator what will change:

- match marked as stats imported
- player stat rows created or replaced
- team aggregates recalculated
- standings recalculated
- Dream Team candidate pool refreshed

### Edit mode

Manual stats edit should support:

- sticky totals row
- validation indicators
- side-by-side team separation
- post-save recalculation summary

### Rankings tab

After import, a rankings surface should show:

- updated standings
- category leaders
- latest changes
- players rising into Dream Team contention

---

## 7.6 Dream Team workspace

The current Dream Team screen is functional but too manual.

The redesigned version should work as a decision support editor.

### Structure

Split by position groups:

- OH
- MB
- S
- OPP
- L

### For each slot, show:

- current selected player
- top algorithmic candidates
- key metrics behind recommendation
- manual override control
- optional explanation note

### Modes

- auto mode preview
- manual override mode
- publish mode

### Required outputs

- current lineup
- difference from auto-calculated lineup
- publish readiness
- linked media and highlight suggestions

This makes Dream Team less like a raw form and more like an editorial selection workflow.

---

## 7.7 Media and Publishing workspace

The gallery should evolve from storage into a publishing pipeline.

### States

- incoming
- tagged
- linked
- featured
- published

### Asset metadata

Each photo or video should optionally link to:

- match
- team
- player
- stage
- court
- feature type

### Benefits

This enables automatic reuse across public pages:

- match highlights on match page
- team gallery on team page
- player visual moments on player page
- Dream Team editorial package

### Editor actions

- bulk tag
- bulk link to match
- mark featured
- reorder highlights
- publish readiness check

---

## 8. Cross-cutting features

## 8.1 Global command palette

Keyboard-first command launcher.

Examples:

- open team Pocket Aces Black
- open match 17
- mark paid
- import stats
- generate roster code
- go to check-in desk

This is one of the highest-value accelerators for staff who use the panel heavily.

## 8.2 Saved views

Every main module should support reusable filters.

Examples:

- unpaid teams
- approved teams not checked in
- matches without stats
- imports needing attention
- media missing links

## 8.3 Sticky bulk action bars

When users select multiple rows or cards, actions should remain visible while scrolling.

## 8.4 Audit timeline

Important changes should be visible on the entity screen:

- status changes
- roster code generation
- stats reimport
- manual stat edits
- Dream Team manual overrides
- media publish events

## 8.5 Notifications and review banners

Use compact non-blocking feedback for:

- successful completion
- warnings
- validation issues
- background recalculation finish

---

## 9. Visual direction for the admin panel

The admin panel should not copy the public Arena Editorial look directly.

It should borrow the discipline, not the theatrical atmosphere.

### Target visual character

- light-first base
- dark anchors for alerts and live operations
- compact cards
- dense tables with excellent alignment
- one primary accent and one warning accent
- monospaced support typography for numeric data

### Recommended visual rules

- brighter default background for long work sessions
- strong border logic instead of heavy blur
- very restrained shadow system
- color only where status or action needs emphasis

### Typography approach

- one compact sans-serif for UI
- one numeric mono companion for scores, IDs and metrics

### Motion approach

- drawer slide-in
- queue card reorder motion
- optimistic micro-feedback for toggles
- no decorative motion loops

---

## 10. Technical architecture direction

The redesign should keep the strengths of the current Django stack.

Do not convert this panel into a heavy SPA by default.

Recommended direction:

- Django templates remain the rendering base
- break screens into reusable partials
- use focused JavaScript for interaction surfaces
- add partial page updates where they remove full reload overhead

### Suggested backend split

Replace the single large custom admin view module with domain-oriented modules.

Suggested structure:

- panel/dashboard_views.py
- panel/team_views.py
- panel/checkin_views.py
- panel/match_views.py
- panel/stats_views.py
- panel/media_views.py
- panel/dreamteam_views.py
- panel/services/
- panel/presenters/

### Suggested frontend split

- panel-base layout
- queue components
- drawer components
- filter bar components
- board components
- stats reconciliation components
- publish workflow components

---

## 11. Success criteria

The redesign is successful when staff can do the following measurably faster:

- approve a team in fewer interactions
- check in a team in under ten seconds after lookup
- detect schedule conflicts before saving
- import stats with fewer manual retries
- publish media without opening multiple modules
- prepare Dream Team selections with clear recommendation support

Qualitative indicators:

- fewer page transitions per task
- fewer operator mistakes
- less need to remember state across screens
- clearer operational priority at login

---

## 12. Implementation roadmap

Phase count is intentionally fixed to 20.

### Phase 1 - Admin redesign audit freeze

Lock the current feature set and document all existing flows, templates, URLs, forms and service dependencies.

Output:

- screen inventory
- current pain-point list
- module dependency map

### Phase 2 - Domain architecture split plan

Define the future module split for views, services, partial templates and JS entry points.

Output:

- target file map
- migration sequence for admin views
- safe refactor boundaries

### Phase 3 - Panel design system foundation

Create the admin UI token system, spacing scale, typography rules, table rules, badge system, alert system and drawer patterns.

Output:

- panel design tokens
- component naming rules
- updated CSS architecture plan

### Phase 4 - New base shell and navigation

Replace the current shell with the new information architecture and role-aware navigation zones.

Output:

- new sidebar and topbar
- module grouping
- reusable content shell

### Phase 5 - Control Room v1

Replace the old KPI dashboard with a queue-based operational dashboard.

Output:

- critical alerts rail
- next two hours module
- unresolved items widgets

### Phase 6 - Team readiness model

Define and surface readiness indicators for each team.

Output:

- payment completeness
- roster completeness
- captain contact completeness
- visual readiness badges

### Phase 7 - Teams workspace v1

Rebuild the teams list into a dual-mode workspace with dense table and saved views.

Output:

- improved filter model
- saved views support
- bulk action bar

### Phase 8 - Team drawer and quick actions

Add the right-side team drawer with high-frequency operational actions.

Output:

- status change from drawer
- payment update
- roster code generation
- quick note entry

### Phase 9 - Registration pipeline board

Build the kanban-style registration flow surface.

Output:

- status columns
- drag or action-based movement
- card-level readiness indicators

### Phase 10 - Check-in desk mode

Create a dedicated check-in interface optimized for tournament day.

Output:

- instant search
- large arrival card
- arrival issue states
- progress tracker

### Phase 11 - Match Operations board foundation

Build the board-based schedule workspace.

Output:

- timeslot by court grid
- compact match cards
- quick match panel

### Phase 12 - Schedule conflict engine

Add validation and warning logic for court, time and team conflicts.

Output:

- pre-save conflict review
- visual warnings
- downstream impact messaging

### Phase 13 - Match detail quick workflow

Connect match cards to high-frequency actions without leaving the board context.

Output:

- status controls
- score quick edit
- stats import jump
- team jump links

### Phase 14 - Stats inbox

Turn stats management into a queue-based workflow instead of a plain match list.

Output:

- waiting for CSV queue
- preview queue
- needs attention queue
- imported queue

### Phase 15 - Reconciliation screen

Create the central preview and mismatch repair surface for CSV imports.

Output:

- parsed row panel
- matched player panel
- warnings rail
- confirm import diff

### Phase 16 - Stats edit and recalculation summary

Upgrade manual stats editing with stronger validation and visible recalculation results.

Output:

- improved edit grid
- post-save summary
- aggregate refresh visibility

### Phase 17 - Rankings and trend surfaces

Expose standings, leaders and latest stat-driven changes as an operator surface.

Output:

- updated rankings module
- leader changes
- Dream Team candidate changes

### Phase 18 - Dream Team decision workspace

Replace the simple slot form with a recommendation-assisted editorial workflow.

Output:

- candidate ranking by position
- auto-fill preview
- override markers
- publish readiness

### Phase 19 - Media and publishing pipeline

Rebuild gallery management into an intake, tagging and publishing workflow.

Output:

- media states
- asset linking to entities
- featured highlight workflow
- bulk tagging

### Phase 20 - Command palette, audit center and hardening

Finish the redesign with staff productivity features and stability work.

Output:

- global command palette
- audit timeline surfaces
- role checks
- performance review
- operator acceptance pass

---

## 13. Recommended implementation order by business value

If the team cannot do all 20 phases continuously, prioritize in this order:

1. Control Room
2. Teams workspace plus drawer
3. Check-in desk
4. Match Operations board
5. Stats inbox plus reconciliation
6. Dream Team workspace
7. Media pipeline
8. command palette plus audit center

This order gives the biggest operational payoff earliest.
