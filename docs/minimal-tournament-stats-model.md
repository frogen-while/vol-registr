# Minimal Tournament Stats Model

## What The Project Collects Today

Registration currently stores only team identity and roster data:

- Team: name, city, league level, instagram, captain, captain email, captain phone.
- Player: first name, last name, jersey number, date of birth.

This is enough for registration, but not enough for a sports frontend with standings, match pages and player leaderboards.

## What To Store For Sports Data

Store raw counts only. Do not save percentages, ratings or composite indexes from the CSV export.

### Match / Team Result Layer

- tournament stage
- group
- court
- home team / away team
- set scores
- sets won / sets lost
- group points awarded

### Team Match Totals

- serve_attempts
- aces
- serve_errors
- attack_attempts
- kills
- attack_errors
- pass_attempts
- perfect_passes
- pass_errors
- blocks

### Player Match Totals

- player number
- player name
- position
- serve_attempts
- aces
- serve_errors
- attack_attempts
- kills
- attack_errors
- pass_attempts
- perfect_passes
- pass_errors
- blocks
- assists
- setting_errors

`assists` and `setting_errors` are optional, but worth keeping because otherwise setters disappear from every leaderboard.

## What Not To Store

Do not persist these CSV columns in the database:

- Serve Rating
- Point Scoring %
- Serve %
- Serve Error %
- Ace %
- Pass Rating
- 3-pass Percent
- Total Pass Error %
- First Ball Side Out %
- FB Pass Rating
- Hitting Efficiency
- Kill %
- Attack Error %
- Block %
- Block Error %
- Total/Game

All of these are derived and should be calculated when rendering the page or generating reports.

## Core Formulas

- Points won = kills + aces + blocks
- Attack efficiency = (kills - attack_errors) / attack_attempts
- Ace % = aces / serve_attempts
- 3-pass % = perfect_passes / pass_attempts
- Pass error % = pass_errors / pass_attempts
- Set ratio = sets_won : sets_lost

Group ranking:

- 2:0 win = 3 points
- 2:1 win = 2 points
- 1:2 loss = 1 point
- 0:2 loss = 0 points

Recommended tie-break order:

1. group points
2. match wins
3. set ratio
4. point ratio if you later track rally points

## How To Read Best Players

Do not use one fully automatic "best player" number across all positions when the data model is small.

Use category leaders first:

1. Top scorer: highest `points won`
2. Best server: highest `ace %` with a minimum-attempt threshold
3. Best receiver: highest `3-pass %` with a minimum-pass threshold
4. Best blocker: highest `blocks`
5. Best setter: highest `assists`, with `setting_errors` as tiebreak

Then choose tournament MVP manually from the shortlist of category leaders plus semifinal/final impact.

This avoids the common problem shown by the sample CSV: a single global formula can overvalue scorers and hide setters or liberos.