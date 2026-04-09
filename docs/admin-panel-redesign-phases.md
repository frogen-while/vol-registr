# Admin Panel Redesign — 10 этапов реализации

> На основе аудита текущего кода vs admin-panel-redesign-blueprint.md (20 фаз).
> Все 18 оригинальных фаз (admin-panel-phases.md) уже выполнены.
> Эти 10 этапов закрывают оставшиеся пробелы до уровня blueprint.

---

## Текущий статус (что уже сделано)

| Модуль | Состояние |
|--------|-----------|
| Каркас, auth, layout | ✅ Работает (base.html, sidebar, topbar, login/logout) |
| Dashboard (KPI) | ✅ 6 карточек, недавние команды, ближайшие матчи |
| Teams list + filters + sort | ✅ Поиск, фильтры, сортировка, batch actions |
| Team CRUD + detail | ✅ Создание/редактирование/удаление + inline players |
| Team status workflow | ✅ Последовательные переходы статусов, batch |
| Check-in | ✅ AJAX toggle, прогресс-бар, сетка карточек |
| Schedule list + grid | ✅ Таблица + grid (корты × таймслоты), фильтры |
| Match CRUD + CSV import | ✅ Формы + CSV с preview + conflict validation |
| Stats import + edit | ✅ Per-team CSV → preview → confirm, inline edit |
| Gallery photos + videos | ✅ CRUD, drag-reorder, bulk add, 2 вкладки |
| Dream Team | ✅ Court layout, 7 слотов, auto-fill, reset |
| CSS design system | ✅ ~1500 строк panel.css, pnl-* токены, компоненты |
| Tests | ✅ 108 тестов, все проходят |

---

## Что ещё НЕ сделано (пробелы относительно blueprint)

### Архитектура
- Все 34 view в одном файле `admin_views.py` (~1100 строк)
- Нет модульного разделения по доменам
- Нет отдельных JS-файлов для панели (всё inline)

### Дизайн-система
- Тёмная тема по умолчанию (blueprint рекомендует light-first)
- Нет spacing scale переменных
- Нет numeric mono шрифта для метрик
- Нет drawer/panel паттерна в CSS

### Навигация
- Плоский sidebar (7 пунктов без группировки)
- Blueprint хочет 5 зон: Control Room, Teams & Registration, Match Operations, Stats & Rankings, Media & Publishing

### Control Room
- Dashboard — статический KPI-отчёт, не операционный экран
- Нет alert rail, queue column, live timeline, intelligence column

### Teams
- Нет readiness модели (payment ✓, roster ✓, contacts ✓, logo ✓, jerseys ✓)
- Нет drawer (detail — полная страница)
- Нет pipeline/kanban доски
- Нет saved views

### Check-in
- Нет поиска по команде
- Нет structured arrival states (только boolean toggle)
- Нет arrival notes, нет large arrival card

### Match Operations
- Нет quick panel при клике на матч
- Нет bracket view для knockout
- Conflict warnings только при submit формы, не визуально

### Stats & Rankings
- Нет queue-based inbox (группировка по состоянию)
- Нет reconciliation layout (3 панели)
- Нет sticky totals в edit mode
- Нет страницы Rankings/Standings в панели

### Dream Team
- Нет candidate ranking по позиции
- Нет preview перед auto-fill
- Нет override markers (auto vs manual)

### Media
- Нет states pipeline (incoming → tagged → linked → featured → published)
- Нет тегирования и привязки к сущностям
- MatchHighlight модель не интегрирована в панель

### Cross-cutting
- Нет command palette
- Нет audit timeline
- Нет role-based views
- Нет saved views
- Нет sticky bulk bar при скролле

---

## 10 этапов реализации

---

### Этап 1: Архитектурный рефакторинг + дизайн-система v2

**Цель**: Разбить монолит `admin_views.py` на доменные модули. Обновить CSS дизайн-систему до уровня blueprint §9.

**Файлы создать**:
- `tournament/panel/` — Python package
- `tournament/panel/__init__.py`
- `tournament/panel/dashboard_views.py`
- `tournament/panel/team_views.py`
- `tournament/panel/checkin_views.py`
- `tournament/panel/match_views.py`
- `tournament/panel/stats_views.py`
- `tournament/panel/media_views.py`
- `tournament/panel/dreamteam_views.py`
- `static/js/panel.js` — вынести inline JS

**Файлы изменить**:
- `tournament/admin_urls.py` — импорты из новых модулей
- `static/css/panel.css` — добавить spacing scale, drawer, light-first option

**Действия**:
1. Создать `tournament/panel/` package, перенести view-функции по доменам
2. Обновить `admin_urls.py` — все import paths
3. Добавить CSS токены: `--pnl-space-1` через `--pnl-space-8`, `--pnl-font-mono`
4. Добавить JetBrains Mono или Source Code Pro как mono-companion
5. Добавить `.pnl-drawer` компонент (slide-in 320px справа, overlay, close)
6. Вынести inline JS (sidebar toggle, batch select, check-in toggle, gallery reorder) в `panel.js`
7. Убедиться что все 108 тестов проходят

**Критерий готовности**: Views разбиты по модулям, CSS drawer работает, mono шрифт подключен, JS вынесен.

---

### Этап 2: Навигация + Control Room v1

**Цель**: Перегруппировать sidebar в 5 зон (blueprint §5). Заменить статический dashboard на операционный Control Room (blueprint §7.1).

**Файлы изменить**:
- `tournament/templates/panel/base.html` — новый sidebar с зонами
- `tournament/panel/dashboard_views.py` — расширить контекст
- `tournament/templates/panel/dashboard.html` → переименовать в `control_room.html`
- `static/css/panel.css` — стили зон, alert rail, queue cards

**Действия**:
1. Sidebar: 5 зон с визуальными разделителями
   - 🏠 Control Room
   - 👥 Teams & Registration (Teams, Check-in)
   - ⚡ Match Operations (Schedule)
   - 📊 Stats & Rankings (Statistics, Rankings)
   - 🎬 Media & Publishing (Gallery, Dream Team)
2. Alert rail: approved teams not checked in, finished matches без stats, matches starting in 2h
3. Queue column: urgency-grouped cards с direct action buttons
4. Live timeline: ближайшие 2 часа (матчи по таймслотам, current time marker)
5. Intelligence column: check-in progress %, stats completion %, latest actions

**Критерий готовности**: Sidebar показывает 5 зон, Control Room имеет alerts + queues + timeline.

---

### Этап 3: Team Readiness Model + Readiness Badges

**Цель**: Добавить computed readiness indicators (blueprint §6). Показывать badge'и готовности на всех team surfaces.

**Файлы изменить**:
- `tournament/models.py` — добавить properties на Team
- `tournament/panel/team_views.py` — аннотировать readiness в queryset
- `tournament/templates/panel/teams_list.html` — readiness column
- `tournament/templates/panel/team_detail.html` — readiness rail
- `static/css/panel.css` — `.pnl-readiness` компонент

**Действия**:
1. Team model properties:
   - `is_roster_complete` — ≥6 игроков
   - `is_contacts_complete` — cap_email + cap_phone заполнены
   - `is_logo_uploaded` — logo не пустой
   - `has_duplicate_jerseys` — проверка дублей номеров в roster
   - `readiness_score` — 0-5 (payment + roster + contacts + logo + jerseys)
2. Readiness badges в teams_list: 5 иконок (✓/✗) рядом с каждой командой
3. Readiness rail на team_detail: горизонтальная полоса с 5 индикаторами
4. Фильтр в teams_list: "Show only incomplete teams"

**Критерий готовности**: Каждая команда показывает 5 readiness badge'ей, можно фильтровать.

---

### Этап 4: Team Drawer + Pipeline Board

**Цель**: Добавить боковой drawer для быстрых действий (blueprint §7.2) и kanban pipeline board (blueprint §7.2 Mode A).

**Файлы создать**:
- `tournament/templates/panel/partials/team_drawer.html` — partial для drawer
- `tournament/templates/panel/teams_pipeline.html` — kanban view

**Файлы изменить**:
- `tournament/panel/team_views.py` — endpoint для drawer data (JSON), pipeline view
- `tournament/admin_urls.py` — новые URL'ы
- `tournament/templates/panel/teams_list.html` — toggle table/pipeline + drawer trigger
- `static/css/panel.css` — pipeline columns, drag cards
- `static/js/panel.js` — drawer open/close, pipeline drag

**Действия**:
1. Team drawer (AJAX partial):
   - Header: name, logo, status badge, readiness rail
   - Quick actions: change status, mark payment, generate roster code, add note
   - Captain contacts section
   - Recent matches (last 3)
   - Кнопка "Open Full Page" → team_detail
2. Pipeline board:
   - 5 колонок: Registered → Awaiting Payment → Paid → Approved → Checked-in
   - Team cards: name, captain, player count, readiness dots
   - Action buttons на карточках (→ next status)
3. Toggle между Table / Pipeline views
4. Pipeline drag-and-drop для смены статуса (с подтверждением)

**Критерий готовности**: Drawer открывается по клику, pipeline board функционален, оба режима переключаются.

---

### Этап 5: Check-in Desk Mode v2

**Цель**: Обновить check-in до уровня blueprint §7.3 — search, arrival card, structured states.

**Файлы изменить**:
- `tournament/panel/checkin_views.py` — search endpoint, arrival states
- `tournament/templates/panel/checkin.html` — search + arrival card + notes
- `static/css/panel.css` — large card, search, arrival states
- `static/js/panel.js` — instant search, arrival card logic

**Действия**:
1. Large search field вверху (instant filter по имени команды / капитана)
2. Arrival card: при клике на команду — большая карточка:
   - Team name (крупно), captain, group
   - Roster completeness (X/6+), payment state
   - Current issues (если есть)
   - Structured arrival buttons: ✅ Complete, ⚠️ Payment Issue, ⚠️ Roster Issue, 🕐 Waiting Coordinator
3. Arrival notes: текстовое поле для заметки при check-in
4. Warning section: блок с командами у которых incomplete readiness
5. Увеличить toggle до touch-friendly размера (min 64×36px)
6. Counter section: checked-in / total + progress bar (уже есть, улучшить)

**Критерий готовности**: Поиск работает мгновенно, arrival card показывает полную информацию, structured states сохраняются.

---

### Этап 6: Match Operations — Quick Panel + Conflict Warnings

**Цель**: Добавить side panel для матчей (blueprint §7.4) и визуальные conflict warnings (blueprint §12).

**Файлы создать**:
- `tournament/templates/panel/partials/match_panel.html` — partial для match side panel

**Файлы изменить**:
- `tournament/panel/match_views.py` — match panel endpoint (JSON/partial), conflict check endpoint
- `tournament/admin_urls.py` — новые URL'ы
- `tournament/templates/panel/schedule_list.html` — panel trigger, conflict badges
- `tournament/admin_forms.py` — расширить conflict detection
- `static/css/panel.css` — match panel, conflict badges
- `static/js/panel.js` — panel open, conflict check on edit

**Действия**:
1. Match quick panel (в drawer):
   - Status controls (SCHED → LIVE → FIN) с кнопками
   - Score quick edit (inline inputs)
   - Court + time display
   - Teams с линками на team pages
   - "Import Stats" jump button
   - "View Stats" jump button (если imported)
2. Conflict warnings:
   - При наведении/открытии edit — live check: court occupied, team double-booked
   - Визуальные badges на grid cards: ⚠️ если есть конфликт
   - Same-team double-booking check (команда играет 2 матча в одно время)
3. Grid card enhancement: добавить stats-imported indicator на карточки

**Критерий готовности**: Panel открывается по клику на матч, статус и счёт меняются inline, конфликты показываются визуально.

---

### Этап 7: Stats Inbox + Reconciliation Layout

**Цель**: Переделать stats list в queue-based inbox (blueprint §7.5). Улучшить reconciliation screen до 3-panel layout.

**Файлы изменить**:
- `tournament/panel/stats_views.py` — группировка по состоянию, reconciliation data
- `tournament/templates/panel/stats_list.html` — queue groups вместо flat table
- `tournament/templates/panel/stats_import.html` — 3-panel layout
- `tournament/templates/panel/stats_edit.html` — sticky totals, team separation
- `static/css/panel.css` — inbox groups, reconciliation panels, sticky totals

**Действия**:
1. Stats inbox — 4 группы:
   - 🔴 Waiting for CSV (finished matches без stats)
   - 🟡 Preview Ready (matches в процессе import)
   - 🟠 Needs Attention (has warnings/errors from last import)
   - 🟢 Imported Successfully (all done)
   Каждая группа — collapsible section с count badge
2. Reconciliation 3-panel layout:
   - Left: parsed CSV rows (raw data)
   - Center: matched players (resolved)
   - Right: warnings rail (unmatched, suspicious)
3. Import diff confirmation:
   - Перед confirm показать: "X player stats will be created, standings will be recalculated, dream team pool refreshed"
4. Stats edit improvements:
   - Sticky totals row (зафиксированная строка с суммами внизу)
   - Visual team separation (2 отдельных блока вместо одной таблицы)
   - Post-save summary: "Updated 12 player rows, recalculated Group A standings"

**Критерий готовности**: Inbox показывает 4 группы, reconciliation в 3 панелях, sticky totals в edit mode.

---

### Этап 8: Rankings Page + Dream Team Upgrade

**Цель**: Добавить страницу Rankings/Standings в панель (blueprint §17). Улучшить Dream Team до decision workspace (blueprint §7.6).

**Файлы создать**:
- `tournament/panel/rankings_views.py` — rankings view
- `tournament/templates/panel/rankings.html` — standings + leaders

**Файлы изменить**:
- `tournament/admin_urls.py` — URL для rankings
- `tournament/templates/panel/base.html` — добавить Rankings в навигацию
- `tournament/panel/dreamteam_views.py` — candidate ranking, preview
- `tournament/templates/panel/dreamteam.html` — candidates, override markers
- `static/css/panel.css` — standings table, candidate list, override markers

**Действия**:
1. Rankings page:
   - Group standings tables (из GroupStanding модели)
   - Category leaders: Top Scorer, Best Server, Top Blocker, Best Receiver
   - "Recalculate All" button → recalculate_standings() + success summary
2. Dream Team upgrade:
   - Candidate ranking: для каждой позиции показать top-5 кандидатов с метриками
   - Auto-fill preview: показать diff "What will change" ПЕРЕД применением
   - Override markers: visual distinction auto (🤖) vs manual (✏️) picks
   - Publish readiness indicator: "All 7 slots filled" / "3 slots empty"
3. Link Dream Team candidates to Rankings leaders

**Критерий готовности**: Rankings page с standings + leaders, Dream Team показывает candidates + preview + override markers.

---

### Этап 9: Media Pipeline + Highlights Integration

**Цель**: Перестроить gallery в publishing pipeline (blueprint §7.7). Интегрировать MatchHighlight в панель.

**Файлы создать**:
- `tournament/templates/panel/highlights.html` — highlights management
- `tournament/panel/highlights_views.py` — highlights CRUD

**Файлы изменить**:
- `tournament/admin_urls.py` — highlights URLs
- `tournament/panel/media_views.py` — media states, entity linking
- `tournament/templates/panel/gallery.html` — states, tags, entity links
- `tournament/templates/panel/base.html` — Highlights в навигацию
- `static/css/panel.css` — media pipeline, highlight cards

**Действия**:
1. Media states на фото/видео:
   - Incoming → Tagged → Linked → Featured (visual pipeline)
   - Status badge на каждом элементе
2. Entity linking:
   - При добавлении/редактировании фото: optional dropdown'ы match, team, player
   - Bulk link: выбрать N фото → привязать к матчу
3. MatchHighlight integration:
   - CRUD для highlights (title, description, match, media_url, order)
   - Link to match page (frontend)
   - Feature/unfeature toggle
4. Bulk tagging:
   - Multi-select фото → assign tag/entity → apply

**Критерий готовности**: Gallery показывает media states, entity linking работает, highlights управляются из панели.

---

### Этап 10: Command Palette + Audit Timeline + Final QA

**Цель**: Добавить keyboard-first command palette (blueprint §8.1), audit timeline (blueprint §8.4), финальная полировка.

**Файлы создать**:
- `tournament/models.py` — AuditEntry model (или использовать django signals)
- `tournament/panel/audit.py` — audit logging helpers

**Файлы изменить**:
- `tournament/templates/panel/base.html` — command palette overlay
- `tournament/panel/*_views.py` — добавить audit logging в key actions
- `static/js/panel.js` — command palette logic, keyboard shortcuts
- `static/css/panel.css` — palette overlay, audit timeline, saved views

**Действия**:
1. Command palette (Ctrl+K / Cmd+K):
   - Fuzzy search: teams, matches, players, pages
   - Quick actions: "mark paid", "import stats", "go to check-in"
   - Recent items
   - Keyboard navigation (↑↓ Enter Esc)
2. Audit timeline:
   - Log key events: status changes, roster code generation, stats import, manual stat edits, dream team changes, media publish
   - Show on entity pages: team_detail → "Recent activity" section
   - Global audit view: sortable/filterable timeline
3. Saved views:
   - Teams: "Unpaid teams", "Approved not checked in", "Incomplete roster"
   - Stats: "Needs import", "Has warnings"
   - Save current filter state → named button
4. Sticky bulk bar: при скролле batch actions bar прилипает к верху
5. Final QA:
   - Все ссылки работают
   - Все формы валидируются
   - Mobile responsive проверен
   - CSRF на всех формах
   - Производительность: prefetch_related где нужно
   - Все тесты проходят + новые тесты для новых features

**Критерий готовности**: Command palette работает по Ctrl+K, audit events логируются и отображаются, saved views доступны, all tests pass.

---

## Зависимости между этапами

```
Этап 1 (архитектура + CSS) ──┬── Этап 2 (навигация + Control Room)
                              ├── Этап 3 (readiness model)
                              └── Этап 6 (match panel)

Этап 2 (Control Room) → данные для alerts используются в Этап 7 (stats inbox)

Этап 3 (readiness) ──┬── Этап 4 (drawer + pipeline)
                      └── Этап 5 (check-in v2)

Этап 4 (drawer) → паттерн drawer используется в Этап 6 (match panel)

Этап 7 (stats inbox) → Этап 8 (rankings)
Этап 8 (rankings) → Этап 8 (dream team upgrade)

Этап 9 (media) — независим после Этапа 1

Этап 10 (command palette + audit) — финальный, после всех
```

---

## Приоритет по бизнес-ценности

Если нельзя сделать все 10 этапов подряд, порядок по ценности:

1. **Этап 1** — фундамент (без него остальное труднее)
2. **Этап 2** — Control Room (самый большой operational payoff)
3. **Этап 3 + 4** — readiness + drawer (ускоряет работу с командами)
4. **Этап 5** — check-in v2 (критично для дня турнира)
5. **Этап 6** — match panel (ускоряет match-day operations)
6. **Этап 7** — stats inbox (ускоряет работу со статистикой)
7. **Этап 8** — rankings + dream team (аналитика + editorial)
8. **Этап 9** — media pipeline (publishing workflow)
9. **Этап 10** — command palette + audit (productivity + accountability)

---

## Стек и решения

| Аспект | Решение |
|--------|---------|
| Backend | Django views split по доменам в `tournament/panel/` |
| Frontend | Django templates + один `panel.js` (vanilla JS) |
| CSS | `panel.css` с `pnl-*` prefix, spacing scale, drawer |
| Шрифты | Inter (UI) + JetBrains Mono (numeric) |
| AJAX | fetch API для drawer, panels, check-in, reorder |
| Drawer | CSS slide-in panel + overlay, открывается по fetch partial |
| Pipeline | CSS grid columns, JS drag (или кнопки), status POST |
| Command Palette | Overlay с fuzzy search, keyboard nav |
| Audit | Simple model (action, entity_type, entity_id, user, timestamp, details JSON) |
