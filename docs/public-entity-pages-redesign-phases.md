# Pocket Aces Tournament - public entity pages redesign blueprint

## 1. Final decision

Style direction is now locked.

Chosen direction: Arena Editorial.

This means the public Team, Match and Player pages will be built as a single editorial sports system with three priorities:

- fast sports readability
- premium arena atmosphere
- clear hierarchy before decoration

Alternative directions are no longer active for this track.

- Court Broadcast is rejected because it would make the product too dashboard-like.
- Club Poster is rejected because it would make Match pages less disciplined and less readable.

Arena Editorial is the best fit because it keeps the speed of a sports product, but gives the pages more identity, more photography, more atmosphere and better emotional weight.

---

## 2. Why Arena Editorial is the right fit

The current state already proved a few important things:

- pure dashboard treatment makes the product feel generic
- heavy blur and modal-first interactions make the product feel unstable
- the user wants pages that feel designed, not patched
- the public entity pages need to work as one family, not as isolated template experiments

Arena Editorial solves this by combining three qualities at once:

- Flashscore-level clarity of stage, score and navigation
- Sofascore-level modularity for stats and cross-linking
- Volleyball World-level premium sports atmosphere and scale

The design goal is not to make the UI busier. The design goal is to make every page feel like a confident event page with an obvious center of gravity.

---

## 3. Design principles

### 3.1 Primary rule

Every page must answer one question in the first screen.

- Team page: who this team is and who matters inside it
- Match page: what happened in the match and why it mattered
- Player page: why this player is important and what defines their profile

### 3.2 Secondary rule

Every page gets exactly one dominant block directly after the hero.

- Team page: Roster Wall
- Match page: Stage Rail
- Player page: Position Fingerprint

### 3.3 Data rule

Stats are always present, but they are not always first.

Order of delivery:

- context
- identity
- key signal
- deep stats

### 3.4 Visual rule

Logos, score, player portraits and important numbers must sit on clean surfaces.

Never put decorative circles, noisy gradients or aggressive masks behind the primary sports assets.

### 3.5 Interaction rule

The UI should feel responsive and physical, but never theatrical.

No full-screen blur as a core mechanic.
No modal dependence for basic discovery.
No animation that hides weak information architecture.

---

## 4. Reference synthesis

### 4.1 From Flashscore

Keep:

- instant score readability
- clear match-to-match navigation
- stage awareness
- court or lane awareness inside the tournament structure

Do not copy:

- dry table-first density
- low-emotion visual language

### 4.2 From Sofascore

Keep:

- section modularity
- sticky section navigation
- comparison logic
- healthy internal entity linking

Do not copy:

- generic all-sports dashboard tone
- overexposed secondary metrics in the first screen

### 4.3 From Volleyball World

Keep:

- premium editorial mood
- larger imagery
- event atmosphere
- better balance of sport and presentation

Do not copy:

- media-heavy structure when it delays access to match or team information

### 4.4 Final synthesis

Pocket Aces should feel like:

- readable as a score product
- designed like an event brand
- linked like a sports database

---

## 5. Arena Editorial visual system

### 5.1 Mood and atmosphere

The pages should feel like a premium tournament evening inside a well-lit sports hall.

Not cyber.
Not esports.
Not default dark dashboard.

Key mood cues:

- warm reflected light from the court floor
- dark controlled contrast in hero and highlight zones
- thin linear geometry inspired by court markings and net structure
- strong portrait photography
- restrained but confident motion

### 5.2 Surface logic

The visual system uses light-first composition with dark anchors.

- light backgrounds for readability and premium feel
- dark sections for scoreboard, match emphasis and stat contrast
- sand and chalk tones to create warmth
- blue and orange as sport accents, not as wallpaper

---

## 6. Exact palette

### 6.1 Core tokens

Use this token map as the base for all public entity pages.

- `--ae-ink-950: #0F1419`
  Main deep contrast color for dark heroes, dark cards and immersive sections.

- `--ae-ink-900: #182028`
  Secondary dark panel color.

- `--ae-ink-800: #24313D`
  Borders, deep rails, dark control states.

- `--ae-chalk-50: #F7F3EC`
  Main page background.

- `--ae-chalk-100: #F0E8DC`
  Secondary light surface.

- `--ae-chalk-200: #E5D7C1`
  Warm separators and soft contrast blocks.

- `--ae-sand-300: #D3BE98`
  Warm surface tint and subtle panel backgrounds.

- `--ae-sand-500: #B48D57`
  Warm editorial accent for badges and small emphasis.

- `--ae-net-500: #1F6FFF`
  Primary interactive accent for links, active nav, comparison rails, info emphasis.

- `--ae-net-600: #1856C8`
  Hover and pressed state for blue interactive elements.

- `--ae-serve-500: #E36B2C`
  Primary warm accent for score emphasis, live or status accents, highlight bars.

- `--ae-serve-600: #B94E17`
  Pressed or deeper orange state.

- `--ae-success-500: #1E9A66`
  Win and positive states.

- `--ae-danger-500: #C94D3F`
  Loss, destructive and error states.

- `--ae-line-soft: rgba(24, 32, 40, 0.10)`
  Light separators.

- `--ae-line-strong: rgba(24, 32, 40, 0.18)`
  Important separators.

- `--ae-shadow-soft: 0 14px 30px rgba(15, 20, 25, 0.08)`
  Base card shadow.

- `--ae-shadow-hero: 0 24px 60px rgba(15, 20, 25, 0.16)`
  Hero and high-emphasis block shadow.

### 6.2 Role mapping

Apply the tokens like this:

- page background: `--ae-chalk-50`
- elevated light cards: `--ae-chalk-100`
- premium light section tint: `--ae-chalk-200`
- dark hero and scoreboard blocks: `--ae-ink-950`
- dark secondary stat panels: `--ae-ink-900`
- links and active anchors: `--ae-net-500`
- score accents and live moments: `--ae-serve-500`
- win and loss labels: `--ae-success-500` and `--ae-danger-500`

### 6.3 Background recipe

Recommended page background stack:

- base color: `--ae-chalk-50`
- top gradient: `radial-gradient(circle at top left, rgba(227, 107, 44, 0.08), transparent 32%)`
- side gradient: `radial-gradient(circle at right 18%, rgba(31, 111, 255, 0.08), transparent 28%)`
- line texture: subtle linear court-grid overlay at 3 to 5 percent opacity

### 6.4 Forbidden palette behaviors

Do not do any of the following:

- cold blue-on-charcoal everywhere
- purple accents
- multiple saturated accents in the same block
- hard black and pure white as the dominant pairing
- glow as a primary visual language

---

## 7. Exact typography

### 7.1 Font stack

Primary display font:

- Bebas Neue

Primary UI and reading font:

- Manrope

Fallback stack:

- `"Segoe UI", Arial, sans-serif`

### 7.2 Usage rules

- Bebas Neue is for page titles, large score numbers, section headlines, short emphatic labels.
- Manrope is for paragraphs, navigation, metadata, tables, buttons and chips.

### 7.3 Scale

Use these target sizes during implementation.

- Hero page title: `clamp(3.6rem, 8vw, 7.2rem)`
- Match score digits: `clamp(3.4rem, 7vw, 6rem)`
- Section headline: `clamp(2rem, 4vw, 3rem)`
- Card title: `clamp(1.15rem, 2vw, 1.5rem)`
- Body copy: `1rem`
- Small UI copy: `0.86rem`
- Meta or chip text: `0.72rem`

### 7.4 Weight and spacing

- Bebas Neue headings: weight 400, letter-spacing `0.01em`, line-height `0.88` to `0.94`
- Manrope body: weight 500, line-height `1.55` to `1.7`
- Manrope meta and controls: weight 700, letter-spacing `0.08em` to `0.14em`, uppercase only for short labels

### 7.5 Numeric behavior

Use tabular numerals for:

- scoreboards
- stat tables
- record strips
- rankings
- timeline values

### 7.6 Forbidden typography behaviors

Do not do any of the following:

- use one font for everything
- use paragraph-sized all-caps text blocks
- make body text overly condensed
- use giant tracking on long strings

---

## 8. Exact motion rules

### 8.1 Motion philosophy

Motion in Arena Editorial is structural, not decorative.

It must explain:

- which block is primary
- which block is becoming active
- how two states connect

### 8.2 Timing tokens

Use these duration tokens:

- `--ae-motion-1: 120ms`
- `--ae-motion-2: 180ms`
- `--ae-motion-3: 260ms`
- `--ae-motion-4: 420ms`

### 8.3 Easing tokens

Use these easing curves:

- `--ae-ease-standard: cubic-bezier(0.22, 1, 0.36, 1)`
- `--ae-ease-soft: cubic-bezier(0.25, 0.8, 0.25, 1)`
- `--ae-ease-sharp: cubic-bezier(0.4, 0, 0.2, 1)`

### 8.4 Allowed animations

- opacity
- transform
- background-color
- border-color
- box-shadow
- clip-path only for controlled reveal moments

### 8.5 Disallowed animations

- continuous pulsing UI outside live badge use
- page-wide blur transitions
- large parallax behavior
- infinite floating cards
- delayed hero animation longer than 600ms total

### 8.6 Block-specific motion

#### Hero reveal

- title: 260ms fade + translateY 18px
- metadata: 180ms fade + translateY 12px
- hero accent card: 260ms fade + translateY 22px

#### Sticky anchor nav

- active pill slide: 180ms using `--ae-ease-standard`
- color change: 120ms

#### Scoreboard

- score digits: 180ms scale from `0.96` to `1`
- set pills: 40ms stagger, max 4 pills visible at once
- live badge: gentle 1.2s opacity pulse only while live

#### Roster wall

- active card expansion: 260ms
- neighboring card soften: 180ms
- local blur cap: 6px
- backdrop dim cap inside section: `rgba(15, 20, 25, 0.14)`

#### Stat charts

- bars draw from zero once on intersection
- ring charts fill once on intersection
- no replay on repeated scroll unless explicitly triggered

### 8.7 Reduced motion contract

When `prefers-reduced-motion: reduce` is active:

- no scale-in
- no blur
- no stagger above 20ms
- no smooth-scrolling animation
- state changes rely on instant reveal and light opacity fade only

---

## 9. Shared component system

Before individual pages, the public redesign must establish a shared component layer.

Required shared components:

- Entity Hero
- Sticky Anchor Nav
- Spotlight Card
- Match Strip
- Stage Rail
- Comparison Bars
- Position Fingerprint Panel
- Editorial Media Block
- Lightweight Timeline
- Stat Table Wrapper

Each of these components must support:

- desktop
- tablet
- mobile
- reduced motion
- empty and partial data states

---

## 10. Team page concept

### 10.1 Purpose

Team page is the face of a squad.

It should feel like entering the team zone, not like opening a spreadsheet with a roster attached.

### 10.2 Hero

The hero should include:

- large clean crest
- team name
- group or bracket position
- record strip
- captain and coach if available
- one dominant metric
- short form strip for last matches

Hero priority:

- identity first
- form second
- deep numbers third

### 10.3 Primary block: Roster Wall

This replaces the current slider-plus-modal pattern.

Desktop behavior:

- 6 to 8 visible player cards
- controlled grid rhythm with one featured card and supporting cards
- active card expands in place
- supporting detail panel appears inside the same wall, not in a global modal

Mobile behavior:

- stacked portrait cards
- tap expands card in flow
- no fullscreen modal

Each player card must expose:

- portrait
- name
- number
- position
- one primary stat
- captain mark if relevant

Expanded state must expose:

- 5 to 6 core stats
- short player hook
- CTA to full Player page

### 10.4 Secondary block: Team Identity Stats

Use four identity dimensions:

- attack conversion
- serve pressure
- block presence
- reception stability

Do not use radar chart as the default V1 solution.

Preferred format:

- four vertical rails or four editorial metric bands
- one sentence explanation per band

### 10.5 Third block: Match Strip

The match history should become a visual strip.

It must show:

- last matches
- next scheduled match if present
- stage
- opponent
- score
- win or loss state
- jump to Match page

Only after this strip should the deeper match table appear.

### 10.6 Fourth block: Team Leaders

Compact leaderboard for:

- points leader
- serve leader
- block leader
- reception leader

This block exists to explain the internal structure of the team.

---

## 11. Match page concept

### 11.1 Purpose

Match page is the event center.

The user must understand the state of the match in 3 to 5 seconds.

### 11.2 Hero

The current scoreboard idea stays, but it becomes more editorial and more disciplined.

Hero content:

- stage
- court
- status
- score by sets
- set pills
- date and time
- prev and next match navigation
- quick links to teams
- storyline line such as straight sets, comeback or tiebreak finish

### 11.3 Primary block: Stage Rail

This is the most important block after the hero.

It must show:

- surrounding matches of the same stage
- lane grouping by court
- current match emphasized more strongly than neighbors
- enough context to understand what led to this match and what comes after

### 11.4 Second block: Match Story

This should explain the match without forcing the user into raw tables first.

It can contain:

- set progression
- momentum swing
- key stretch of points
- short summary copy

### 11.5 Third block: Team Comparison

Use 6 to 8 strong comparison metrics only.

No metric spam.

Each metric must have:

- left team value
- right team value
- wide comparison rail
- concise label

### 11.6 Fourth block: Player Leaders

Before full tables, show leaders such as:

- top scorer
- best server
- best blocker
- best receiver

Only after that comes the deep player table and filters.

### 11.7 Fifth block: MVP and media

The MVP block should feel ceremonial.

Media and highlights should feel editorial, not like an afterthought gallery.

---

## 12. Player page concept

### 12.1 Purpose

Player page is the profile of a sports personality, not just a record page.

### 12.2 Public flow decision

Player page returns as a first-class public destination.

The team page should spotlight players.
The player page should own the depth.

### 12.3 Hero

Hero content:

- large portrait
- player name
- number
- position
- team link
- 2 to 3 achievement chips
- one role-based statement such as top blocker or serve leader

### 12.4 Primary block: Position Fingerprint

The main fingerprint must change by role.

Setter emphasis:

- assists
- decision quality
- serve pressure

Middle blocker emphasis:

- blocks
- quick attack efficiency
- points per set

Outside or opposite emphasis:

- kills
- attack efficiency
- total point creation

Libero emphasis:

- reception quality
- digs or receive stability proxy
- error rate

### 12.5 Second block: Season Snapshot

Show:

- totals
- rank inside team
- rank inside tournament
- recent form

### 12.6 Third block: Match Timeline

The match log moves lower.

It should become a readable timeline with:

- opponent
- stage
- score
- key stat line
- link to Match page

### 12.7 Fourth block: Recognition

Awards remain, but they become secondary content.

---

## 13. Cross-page system rules

### 13.1 Required entity flow

- Hub -> Match
- Hub -> Teams
- Teams -> Team
- Team -> Player
- Match -> Team
- Match -> Player
- Player -> Team
- Player -> Related Match

### 13.2 Preview rule

Every page must preview the next deeper entity.

Examples:

- Team page previews players
- Match page previews teams and player leaders
- Player page previews recent matches

### 13.3 Breadcrumb rule

Each entity page should have light contextual return links, but not heavy breadcrumb noise.

---

## 14. What stays from the current implementation

Keep and refine:

- scoreboard direction on Match page
- previous and next match navigation
- anchor nav logic
- comparison bar logic
- existing data helpers that already produce match or team metrics

Rebuild completely:

- Team page roster interaction
- Player page public role and order of sections
- visual hierarchy of Team and Player pages
- shared motion system

Remove as debt:

- slider-plus-modal coupling as the central Team page interaction
- global blur feeling
- decorative backgrounds behind logos

---

## 15. Detailed implementation phases

The roadmap below is intentionally long and granular. It is meant to remove improvisation during implementation.

### Phase 01. Style lock and token map

Output:

- Arena Editorial marked as final direction
- palette tokens approved
- typography tokens approved
- motion tokens approved

### Phase 02. Public UI audit against the new direction

Output:

- map old blocks to keep, rebuild or delete
- mark which current selectors and template zones can be reused
- identify all current roster, player and match interaction debt

### Phase 03. Shared visual foundations

Output:

- background system
- surface system
- border and shadow rules
- editorial spacing rhythm

### Phase 04. Shared typography implementation spec

Output:

- display hierarchy
- body hierarchy
- scoreboard number rules
- table number behavior

### Phase 05. Shared motion implementation spec

Output:

- reveal patterns
- scoreboard emphasis pattern
- roster expansion pattern
- reduced motion fallback contract

### Phase 06. Component inventory and decomposition

Output:

- final list of reusable public components
- component ownership map for CSS, template and JS layers

### Phase 07. Public navigation cleanup

Output:

- clearer entity return paths
- cleaner top navigation consistency
- shared anchor navigation behavior aligned across all three pages

### Phase 08. Team page information architecture

Output:

- final section order
- hero content contract
- roster wall data contract
- team leader block contract

### Phase 09. Team hero redesign

Output:

- identity-led hero
- form strip
- dominant team metric
- cleaner crest treatment

### Phase 10. Roster Wall structural rebuild

Output:

- remove roster slider as primary discovery model
- build expandable wall behavior
- define desktop and mobile interaction separately

### Phase 11. Roster Wall interaction polish

Output:

- in-place expansion
- local dim and blur limits
- keyboard and focus behavior
- direct jump to Player page

### Phase 12. Team identity metrics block

Output:

- four identity metrics
- explanatory copy treatment
- comparison-friendly stat presentation

### Phase 13. Team match strip and deep archive

Output:

- visual match strip for recent and next matches
- secondary deep archive table below
- better transition from team context into match context

### Phase 14. Match page information architecture

Output:

- final order: hero -> stage rail -> story -> comparison -> leaders -> deep stats -> mvp/media

### Phase 15. Match hero refinement

Output:

- improved scoreboard emphasis
- storyline line
- controlled metadata strip
- stronger current-state readability

### Phase 16. Stage Rail build

Output:

- lane-based context for stage matches
- highlighted current match
- navigation logic for surrounding matches

### Phase 17. Match story and leaders

Output:

- set progression block
- leaders before full tables
- cleaner transition into deep stats

### Phase 18. Player page information architecture

Output:

- player route returns as first-class public route
- new section order
- role-based fingerprint rules

### Phase 19. Player hero and fingerprint

Output:

- premium player hero
- position-aware stat emphasis
- achievement chips and narrative hook

### Phase 20. Player timeline and recognition layers

Output:

- readable match timeline
- awards as secondary content
- relation blocks back to Team and Match pages

### Phase 21. Cross-page linking and entity loops

Output:

- strong internal linking network
- each page previews the next entity naturally
- no public dead-end pages

### Phase 22. Empty, partial and fallback states

Output:

- no-photo fallback
- partial stats fallback
- pre-match and post-match state logic
- graceful handling when Dream Team or leaders are unavailable

### Phase 23. Mobile and tablet adaptation

Output:

- no desktop interaction leaking into mobile
- no modal dependence on mobile
- proper spacing, touch targets and content order

### Phase 24. SEO and social layer

Output:

- consistent titles and descriptions
- better social card hierarchy
- stable public indexing behavior for Team, Match and Player pages

### Phase 25. Final polish, QA and release validation

Output:

- reveal performance check
- no excessive layout shift
- image loading strategy
- reduced motion validation
- remove legacy visual leftovers
- normalize logo treatment
- normalize badge, chip and stat styling
- microcopy cleanup
- better section labels
- better narrative text for match and player context
- full desktop review
- tablet review
- mobile review
- regression pass on interactions and navigation

---

## 16. Execution order recommendation

If implementation starts now, the correct order is:

1. Style lock and tokens.
2. Team page rebuild first.
3. Shared CSS and JS layer extraction.
4. Match page rebuild on the new system.
5. Player page return as a first-class public page.
6. Cross-page polish and SEO.

Reason:

The current Team page is the main source of interaction debt. Once it is rebuilt cleanly, Match and Player become much easier to align.

---

## 17. Final summary

Arena Editorial means the product should feel like this:

- Team page = squad identity and internal hierarchy
- Match page = event and match context
- Player page = personality and performance fingerprint

The target is not more effects.
The target is stronger hierarchy, cleaner surfaces, better sports atmosphere and faster understanding.
