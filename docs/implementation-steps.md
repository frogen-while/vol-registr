# Pocket Aces Tournament Platform — Детальный план реализации

> Документ оптимизирован для автоматического выполнения ИИ-агентом.
> Каждый шаг является атомарным действием с чёткими входами, выходами и критериями готовности.
> Порядок шагов учитывает зависимости — не перескакивай вперёд.

---

## КОНТЕКСТ ПРОЕКТА

### Что уже есть и работает

- **Регистрация**: Team + Player модели, 3-step форма, оплата через BLIK, email-уведомления
- **Демо-фронтенд**: 6 preview-страниц с мок-данными из `_sports_demo_bundle()` в `views.py`
  - `tournament_preview` — хаб: standings (Groups/Overall toggle), schedule (time-slot grid, 3 корта), highlights
  - `teams_preview` — список команд по группам (4 группы × 3 команды)
  - `dream_team_preview` — Dream Team с CSS-площадкой и 7 позициями
  - `match_preview` — детальная страница матча (Hero, scoreboard, team stats comparison, player stats table, highlights)
  - `team_preview` — команда (roster, match history, team stats cards)
  - `player_preview` — игрок (profile, match log, stat cards)
- **Стилевая система**: `sports-preview.css` с `--sp-*` переменными, clip-path, glass-morphism, тёмная тема
- **JS**: `sports-preview.js` (toggle panels, IntersectionObserver, GSAP reveals), `navbar.js` (EN/PL i18n, 600+ ключей)
- **Миграции**: есть Sector, Match, GameSet, MatchEvent — но модели удалены из `models.py` (миграции 0004–0010 в базе)
- **Admin**: полноценный для Team/Player с batch actions

### Что НЕ работает / нет

- Нет моделей для stats (PlayerMatchStats, DreamTeamEntry, MVPSelection, MatchHighlight, Stage)
- Нет CSV-импорта
- Все preview-страницы на мок-данных, ни одна не подключена к БД
- Нет SEO-метаданных на спортивных страницах
- Нет экспорта PDF/PNG
- Стрим-плеер не реализован (fallback уже есть в дизайне)
- Некоторые CSS-классы определены, но не используются (`.sp-bracket-*`, `.sp-scoreboard`, `.sp-kpi-*`)

### Файловая карта проекта

```
tournament/
  models.py          — Team, Player (нужно добавить 8+ моделей)
  views.py           — _sports_demo_bundle() ~1500 LOC мок-данных + 6 preview views
  services.py        — get_available_slots(), register_team()
  constants.py       — MAX_TOURNAMENT_SLOTS, PAYMENT_*, LEAGUE_LEVEL_*
  forms.py           — TeamRegistrationForm, PlayerForm
  admin.py           — TeamAdmin, PlayerAdmin
  urls.py            — 13 маршрутов
  templates/tournament/
    tournament_preview.html
    teams_preview.html
    dream_team_preview.html
    (match_preview.html, team_preview.html, player_preview.html — ещё не найдены, рендерятся из views)
static/
  css/sports-preview.css
  js/sports-preview.js, navbar.js, config.js
```

### Формат турнира

- 12 команд, 4 группы по 3
- Этапы: Groups → Quarter-finals → Semi-finals (1–4, 5–8, 9–12) → Placement finals → Final
- 3 корта = до 3 параллельных матчей
- Очки: 2:0 win = 3 pts, 2:1 win = 2 pts, 1:2 loss = 1 pt, 0:2 loss = 0 pts

---

## ФАЗА 1: МОДЕЛИ ДАННЫХ

### 1.1 Вернуть и расширить модель Match в models.py

**Файл**: `tournament/models.py`

**Действия**:
1. Добавить `MATCH_STATUS_CHOICES` в `constants.py`: `SCHEDULED`, `LIVE`, `FINISHED`, `POSTPONED`
2. Добавить `STAGE_CHOICES` в `constants.py`: `GROUP`, `QF`, `SF_1_4`, `SF_5_8`, `SF_9_12`, `PLACE_11`, `PLACE_9`, `PLACE_7`, `PLACE_5`, `PLACE_3`, `FINAL`
3. Добавить `COURT_CHOICES` в `constants.py`: `1`, `2`, `3`
4. Создать модель `Match` в `models.py` со следующими полями:
   - `stage` — CharField с STAGE_CHOICES
   - `group` — CharField(max_length=1, blank=True) для групповых матчей ('A', 'B', 'C', 'D')
   - `court` — IntegerField с COURT_CHOICES
   - `start_time` — DateTimeField
   - `team_a` — ForeignKey(Team, related_name='matches_as_home')
   - `team_b` — ForeignKey(Team, related_name='matches_as_away')
   - `score_a` — IntegerField(default=0) — сеты выигранные team_a
   - `score_b` — IntegerField(default=0) — сеты выигранные team_b
   - `status` — CharField с MATCH_STATUS_CHOICES, default='SCHEDULED'
   - `match_number` — IntegerField(unique=True) — глобальный номер матча в турнире (1–28)
   - `stats_imported` — BooleanField(default=False)
   - `stats_imported_at` — DateTimeField(null=True, blank=True)
5. Добавить `Meta`: `ordering = ['start_time', 'court']`, `db_table = 'matches'`
6. Добавить `__str__`: `f"M{self.match_number}: {self.team_a} vs {self.team_b}"`
7. Добавить property `winner` → Team или None
8. Добавить property `loser` → Team или None
9. Добавить property `is_finished` → bool
10. Добавить property `set_scores_display` → str (e.g. "2:1")

**Проверка**: `python manage.py makemigrations --dry-run` — без ошибок.

### 1.2 Создать модель GameSet

**Файл**: `tournament/models.py`

**Действия**:
1. Создать модель `GameSet`:
   - `match` — ForeignKey(Match, related_name='sets')
   - `set_number` — PositiveIntegerField (1, 2, 3)
   - `score_a` — PositiveIntegerField(default=0)
   - `score_b` — PositiveIntegerField(default=0)
2. `Meta`: `ordering = ['set_number']`, `unique_together = [('match', 'set_number')]`

**Проверка**: Модель импортируется без ошибок.

### 1.3 Создать модель PlayerMatchStats

**Файл**: `tournament/models.py`

**Действия**:
1. Добавить `POSITION_CHOICES` в `constants.py`: `OH` (Outside Hitter), `MB` (Middle Blocker), `S` (Setter), `OPP` (Opposite), `L` (Libero)
2. Создать модель `PlayerMatchStats`:
   - `match` — ForeignKey(Match, related_name='player_stats')
   - `player` — ForeignKey(Player, related_name='match_stats')
   - `team` — ForeignKey(Team, related_name='match_player_stats')
   - `position` — CharField с POSITION_CHOICES
   - `jersey_number` — PositiveIntegerField
   - `serve_attempts` — PositiveIntegerField(default=0)
   - `aces` — PositiveIntegerField(default=0)
   - `serve_errors` — PositiveIntegerField(default=0)
   - `attack_attempts` — PositiveIntegerField(default=0)
   - `kills` — PositiveIntegerField(default=0)
   - `attack_errors` — PositiveIntegerField(default=0)
   - `pass_attempts` — PositiveIntegerField(default=0)
   - `perfect_passes` — PositiveIntegerField(default=0)
   - `pass_errors` — PositiveIntegerField(default=0)
   - `blocks` — PositiveIntegerField(default=0)
   - `assists` — PositiveIntegerField(default=0)
   - `setting_errors` — PositiveIntegerField(default=0)
3. `Meta`: `unique_together = [('match', 'player')]`, `db_table = 'player_match_stats'`
4. Добавить computed properties (НЕ сохранять в БД, считать на лету):
   - `points_won` → kills + aces + blocks
   - `attack_efficiency` → (kills - attack_errors) / attack_attempts или None если 0 попыток
   - `ace_pct` → aces / serve_attempts или None
   - `pass_3_pct` → perfect_passes / pass_attempts или None
   - `pass_error_pct` → pass_errors / pass_attempts или None

**Проверка**: Все properties возвращают корректные значения при нулевых делителях (return None).

### 1.4 Создать модель TeamMatchStats (агрегат)

**Файл**: `tournament/models.py`

**Действия**:
1. Создать модель `TeamMatchStats`:
   - `match` — ForeignKey(Match, related_name='team_stats')
   - `team` — ForeignKey(Team, related_name='match_team_stats')
   - Все те же числовые поля что и PlayerMatchStats (serve_attempts, aces, ... blocks)
   - БЕЗ assists/setting_errors (это командный агрегат)
2. `Meta`: `unique_together = [('match', 'team')]`, `db_table = 'team_match_stats'`

**Проверка**: Модель импортируется.

### 1.5 Создать модель GroupStanding (денормализованная таблица группы)

**Файл**: `tournament/models.py`

**Действия**:
1. Создать модель `GroupStanding`:
   - `team` — OneToOneField(Team, related_name='standing')
   - `group` — CharField(max_length=1) — 'A', 'B', 'C', 'D'
   - `played` — PositiveIntegerField(default=0)
   - `wins` — PositiveIntegerField(default=0)
   - `losses` — PositiveIntegerField(default=0)
   - `sets_won` — PositiveIntegerField(default=0)
   - `sets_lost` — PositiveIntegerField(default=0)
   - `points` — PositiveIntegerField(default=0)
   - `rank_in_group` — PositiveIntegerField(default=0)
2. `Meta`: `ordering = ['group', 'rank_in_group']`, `db_table = 'group_standings'`

**Проверка**: При создании 12 записей — у каждой группы ровно 3 записи.

### 1.6 Создать модель DreamTeamEntry

**Файл**: `tournament/models.py`

**Действия**:
1. Создать модель `DreamTeamEntry`:
   - `position` — CharField с POSITION_CHOICES
   - `slot` — CharField(max_length=20) — CSS-позиция на площадке: `front-left`, `front-center`, `front-right`, `back-left`, `back-center`, `back-right`, `libero`
   - `player` — ForeignKey(Player, related_name='dream_team_entries')
   - `team` — ForeignKey(Team)
   - `metric_label` — CharField(max_length=50) — "12 kills" / "5 aces" etc.
   - `metric_value` — FloatField — для сортировки
   - `is_auto` — BooleanField(default=True) — авторасчёт vs ручной
2. `Meta`: `db_table = 'dream_team'`

**Проверка**: 7 записей на турнир — по одной на позицию.

### 1.7 Создать модель MVPSelection

**Файл**: `tournament/models.py`

**Действия**:
1. Добавить `MVP_TYPE_CHOICES` в `constants.py`: `MATCH_MVP`, `TOURNAMENT_MVP`
2. Создать модель `MVPSelection`:
   - `mvp_type` — CharField с MVP_TYPE_CHOICES
   - `player` — ForeignKey(Player, related_name='mvp_selections')
   - `team` — ForeignKey(Team)
   - `match` — ForeignKey(Match, null=True, blank=True) — для match MVP
   - `reason` — CharField(max_length=200, blank=True)
   - `is_auto` — BooleanField(default=True)
3. `Meta`: `db_table = 'mvp_selections'`

**Проверка**: Для MATCH_MVP match обязателен; для TOURNAMENT_MVP match = None.

### 1.8 Создать модель MatchHighlight

**Файл**: `tournament/models.py`

**Действия**:
1. Создать модель `MatchHighlight`:
   - `match` — ForeignKey(Match, related_name='highlights', null=True, blank=True) — может быть турнирный
   - `title` — CharField(max_length=200)
   - `description` — TextField(blank=True)
   - `media_url` — URLField(blank=True) — ссылка на видео/фото
   - `thumbnail_url` — URLField(blank=True)
   - `order` — PositiveIntegerField(default=0)
2. `Meta`: `ordering = ['order']`, `db_table = 'match_highlights'`

**Проверка**: Сортировка по order работает.

### 1.9 Создать и применить миграцию

**Команды**:
```bash
python manage.py makemigrations tournament
python manage.py migrate
```

**Проверка**:
1. Миграция создаётся без конфликтов с существующими 0001–0010
2. `python manage.py migrate` завершается без ошибок
3. `python manage.py shell -c "from tournament.models import Match, PlayerMatchStats, GroupStanding; print('OK')"` — OK

### 1.10 Зарегистрировать новые модели в admin.py

**Файл**: `tournament/admin.py`

**Действия**:
1. `MatchAdmin`:
   - `list_display`: match_number, stage, team_a, team_b, score_a, score_b, status, court, start_time, stats_imported
   - `list_filter`: stage, status, court, stats_imported
   - `search_fields`: team_a__name, team_b__name
   - `readonly_fields`: stats_imported_at
   - Inline: `GameSetInline` (TabularInline, extra=0)
2. `PlayerMatchStatsAdmin`:
   - `list_display`: player, team, match, position, kills, aces, blocks, points_won
   - `list_filter`: match, team, position
   - `search_fields`: player__first_name, player__last_name
3. `TeamMatchStatsAdmin`:
   - `list_display`: team, match, kills, aces, blocks
   - `list_filter`: match
4. `GroupStandingAdmin`:
   - `list_display`: team, group, played, wins, losses, sets_won, sets_lost, points, rank_in_group
   - `list_filter`: group
5. `DreamTeamEntryAdmin`:
   - `list_display`: position, slot, player, team, metric_label, is_auto
6. `MVPSelectionAdmin`:
   - `list_display`: mvp_type, player, team, match, is_auto
   - `list_filter`: mvp_type, is_auto
7. `MatchHighlightAdmin`:
   - `list_display`: title, match, order
   - `list_editable`: order

**Проверка**: Django admin показывает все модели без ошибок; можно создать запись вручную.

---

## ФАЗА 2: CSV-ИМПОРТ

### 2.1 Определить формат CSV и создать маппинг полей

**Файл**: Создать `tournament/csv_mapping.py`

**Действия**:
1. Определить `PLAYER_STATS_CSV_COLUMNS` — маппинг заголовков CSV из SoloStats Live к полям модели:
   ```python
   CSV_TO_MODEL = {
       'Player Name': 'player_name',       # parse to first_name, last_name
       'Jersey': 'jersey_number',
       'Position': 'position',
       'Serve Attempts': 'serve_attempts',
       'Aces': 'aces',
       'Serve Errors': 'serve_errors',
       'Attack Attempts': 'attack_attempts',
       'Kills': 'kills',
       'Attack Errors': 'attack_errors',
       'Pass Attempts': 'pass_attempts',
       'Perfect Passes': 'perfect_passes',
       'Pass Errors': 'pass_errors',
       'Blocks': 'blocks',
       'Assists': 'assists',
       'Setting Errors': 'setting_errors',
   }
   ```
2. Определить `REQUIRED_COLUMNS` — минимальные обязательные заголовки
3. Определить `TEAM_RESULT_CSV_COLUMNS` — маппинг для мета-результата матча:
   ```python
   MATCH_META_COLUMNS = {
       'Team Name': 'team_name',
       'Sets Won': 'sets_won',
       'Sets Lost': 'sets_lost',
       'Set 1': 'set_1_score',
       'Set 2': 'set_2_score',
       'Set 3': 'set_3_score',
   }
   ```

**Проверка**: Файл импортируется без ошибок.

### 2.2 Создать CSV-парсер с валидацией

**Файл**: Создать `tournament/csv_import.py`

**Действия**:
1. Функция `parse_csv(file_obj) → dict`:
   - Читает файл через `csv.DictReader`
   - Нормализует заголовки (strip, lowercase comparison)
   - Проверяет наличие REQUIRED_COLUMNS
   - Для каждой строки:
     - Валидирует числовые поля (≥ 0, целые)
     - Валидирует position через POSITION_CHOICES
     - Парсит player_name → first_name + last_name
   - Возвращает `{'rows': [...], 'errors': [...], 'warnings': [...]}`
2. Функция `validate_against_db(parsed_rows, match_id) → dict`:
   - Проверяет что match_id существует
   - Проверяет что team names матчат team_a/team_b матча
   - Проверяет что jersey numbers матчат зарегистрированным игрокам
   - Собирает `{'valid_rows': [...], 'unmatched_players': [...], 'errors': [...]}`
3. Все ошибки — человекочитаемые строки на английском

**Проверка**: Парсинг корректного CSV → 0 ошибок. Парсинг CSV с пропущенными полями → список warnings. Парсинг CSV с невалидными данными → список errors.

### 2.3 Создать сервис импорта с preview и confirm

**Файл**: `tournament/services.py` (расширить)

**Действия**:
1. Функция `preview_csv_import(file_obj, match_id) → dict`:
   - Вызывает `parse_csv(file_obj)`
   - Вызывает `validate_against_db(parsed, match_id)`
   - Возвращает `{'preview': [...], 'errors': [...], 'warnings': [...], 'can_import': bool}`
   - НЕ коммитит в БД
2. Функция `confirm_csv_import(file_obj, match_id) → dict`:
   - Вызывает preview внутри
   - Если `can_import == False` → raise ValueError
   - В `@transaction.atomic`:
     a. Удалить существующие PlayerMatchStats для match_id (перезапись)
     b. Удалить существующие TeamMatchStats для match_id
     c. Создать PlayerMatchStats для каждого valid_row
     d. Агрегировать и создать TeamMatchStats для team_a и team_b
     e. Обновить Match.score_a, score_b из CSV мета-строк сетов
     f. Создать/обновить GameSet записи
     g. Установить Match.stats_imported = True, stats_imported_at = now()
   - Возвращает `{'imported': count, 'warnings': [...]}`
3. Функция `recalculate_standings()`:
   - Пересчитать GroupStanding из всех GROUP-матчей со статусом FINISHED
   - Для каждого матча: 3 pts (2:0), 2 pts (2:1), 1 pt (1:2), 0 pts (0:2)
   - Ранжировать внутри группы по: points → wins → set ratio
4. Функция `recalculate_dream_team()`:
   - Собрать все PlayerMatchStats по всему турниру
   - Для каждой позиции выбрать лучшего:
     - OH/OPP: максимум kills
     - MB: максимум blocks
     - S: максимум assists
     - L: максимум perfect_passes
   - Удалить старые DreamTeamEntry с is_auto=True
   - Создать новые 7 записей (OH×2, MB×2, OPP, S, L)
   - Присвоить slot по позиции:
     - OH → front-left, back-right
     - MB → front-center, back-center
     - OPP → front-right
     - S → back-left
     - L → libero

**Проверка**: 
- preview_csv_import не меняет БД (count until и count after равны)
- confirm_csv_import создаёт корректное количество PlayerMatchStats
- Повторный confirm_csv_import для того же матча → старые записи удалены, новые созданы
- recalculate_standings выдаёт корректные очки для всех 12 команд

### 2.4 Создать admin-view для CSV-импорта

**Файл**: `tournament/admin.py` (расширить MatchAdmin)

**Действия**:
1. Добавить в MatchAdmin кастомный action `import_csv_stats`:
   - Если один матч выбран → перенаправить на страницу импорта
   - Если несколько → ошибка "Select exactly one match"
2. Создать custom admin view `match_csv_import_view(request, match_id)`:
   - GET: показать форму загрузки с информацией о матче
   - POST с `action=preview`: вызвать `preview_csv_import`, показать результат
   - POST с `action=confirm`: вызвать `confirm_csv_import`, показать результат, перенаправить назад
3. Зарегистрировать URL через `get_urls()` в MatchAdmin
4. Шаблон: `tournament/admin/csv_import.html` — минималистичный, наследует `admin/base_site.html`

**Проверка**: 
- Админ может загрузить CSV файл через UI
- Preview показывает разобранные данные
- Confirm создаёт записи в БД
- Повторный импорт перезаписывает данные

### 2.5 Автоматический пересчёт после импорта

**Файл**: `tournament/services.py`

**Действия**:
1. В конце `confirm_csv_import()` вызывать:
   - `recalculate_standings()` — если импортирован GROUP-матч
   - `recalculate_dream_team()` — всегда
2. Логировать результат пересчёта

**Проверка**: После импорта CSV для группового матча — GroupStanding обновлён. DreamTeamEntry содержит 7 записей.

---

## ФАЗА 3: РАСПИСАНИЕ И SEED ДАННЫХ

### 3.1 Создать management command для заполнения расписания турнира

**Файл**: Создать `tournament/management/commands/seed_schedule.py`

**Действия**:
1. Создать `Command(BaseCommand)` с `handle(self, *args, **options)`:
2. Создать 28 Match записей (точная копия из `_sports_demo_bundle()`):
   - 12 групповых матчей (4 группы × 3 матча): время 09:00–10:20
   - 4 QF: время 11:00
   - 2 SF 1–4: время 12:00
   - 2 SF 5–8: время 12:00
   - 2 SF 9–12: время 12:00
   - Placement: 11th, 9th, 7th → время 13:20
   - 5th, 3rd → время 14:00
   - Final → время 15:00
3. Команды привязывать по name из БД (через `Team.objects.get(name=...)`)
4. Если команд нет — пропускать, выводить warning
5. Если команды есть, но match уже создан (по match_number) — skip
6. Дата турнира — параметр `--date` (default: ближайшая суббота)

**Проверка**: `python manage.py seed_schedule --date 2026-07-11` создаёт 28 матчей.

### 3.2 Создать management command для заполнения GroupStanding

**Файл**: Создать `tournament/management/commands/seed_groups.py`

**Действия**:
1. Назначить 12 команд по 4 группам (A, B, C, D) по 3 команды
2. Создать GroupStanding записи с начальными нулями
3. Обновить Team.group_name из 'A'–'D'

**Проверка**: 12 GroupStanding, каждая группа содержит ровно 3.

### 3.3 Создать management command для seed демо-статистики

**Файл**: Создать `tournament/management/commands/seed_demo_stats.py`

**Действия**:
1. Для каждого завершённого матча (если есть) — заполнить PlayerMatchStats из мок-данных `_sports_demo_bundle()`
2. Заполнить GameSet записи
3. Вызвать `recalculate_standings()`
4. Вызвать `recalculate_dream_team()`
5. Создать MVPSelection записей (match MVP для каждого матча, tournament MVP)
6. Создать MatchHighlight записей (3–5 штук)

**Проверка**: После seed — все Public API views работают с реальными БД-данными.

---

## ФАЗА 4: VIEWS — ПЕРЕХОД С МОКА НА БД

### 4.1 Создать сервис-слой для чтения спортивных данных

**Файл**: `tournament/services.py` (расширить) или создать `tournament/sports_data.py`

**Действия**:
1. Функция `get_schedule_slots(date=None) → list[dict]`:
   - Запрос: `Match.objects.select_related('team_a', 'team_b').order_by('start_time', 'court')`
   - Группировка по `start_time` → list of `{'time': '09:00', 'games': [...]}`
   - Каждый game: `{'court': 1, 'stage': 'Group A', 'team_a': ..., 'team_b': ..., 'score': '2:1', 'status': ...}`
2. Функция `get_standings(view='groups') → dict`:
   - `view='groups'`: `GroupStanding.objects.select_related('team').values(...)` grouped by group
   - `view='overall'`: все GroupStanding отсортированные по points desc, set ratio
3. Функция `get_match_detail(match_id) → dict`:
   - Match + GameSets + PlayerMatchStats (обе команды) + TeamMatchStats
   - Derived metrics (attack efficiency, ace %, etc.)
   - Comparison bars для team vs team
4. Функция `get_team_detail(team_id) → dict`:
   - Team + roster + match history + aggregated stats across all matches
5. Функция `get_player_detail(player_id) → dict`:
   - Player + match log (stats per match) + cumulative stats + rank in category
6. Функция `get_dream_team() → list`:
   - DreamTeamEntry.objects.select_related('player', 'team')
   - Mapping slot → player info
7. Функция `get_highlights() → list`:
   - MatchHighlight.objects.all()[:10]
8. Функция `get_mvp(mvp_type) → dict`:
   - MVPSelection.objects.filter(mvp_type=mvp_type).select_related('player', 'team')

**Проверка**: Каждая функция возвращает корректные данные при наличии seed data.

### 4.2 Обновить tournament_preview view

**Файл**: `tournament/views.py`

**Действия**:
1. Заменить `_sports_demo_bundle()` вызовы на реальные сервис-функции:
   ```python
   def tournament_preview(request):
       context = {
           'standings': get_standings('groups'),
           'overall_standings': get_standings('overall'),
           'schedule_slots': get_schedule_slots(),
           'highlights': get_highlights(),
       }
       return render(request, 'tournament/tournament_preview.html', context)
   ```
2. Сохранить fallback на пустые списки если данных нет

**Проверка**: Страница рендерится с данными из БД. Без seed data — рендерится с пустыми секциями.

### 4.3 Обновить teams_preview view

**Файл**: `tournament/views.py`

**Действия**:
1. Заменить мок-данные на:
   ```python
   def teams_preview(request):
       context = {
           'standings': get_standings('groups'),
       }
       return render(request, 'tournament/teams_preview.html', context)
   ```

**Проверка**: Показывает 4 группы с реальными командами из БД.

### 4.4 Обновить dream_team_preview view

**Файл**: `tournament/views.py`

**Действия**:
1. Заменить мок-данные:
   ```python
   def dream_team_preview(request):
       context = {
           'dream_team': get_dream_team(),
       }
       return render(request, 'tournament/dream_team_preview.html', context)
   ```

**Проверка**: 7 позиций отображаются на площадке.

### 4.5 Обновить match_preview view — принять match_id

**Файл**: `tournament/views.py` + `tournament/urls.py`

**Действия**:
1. Изменить URL: `path('match/<int:match_id>/', views.match_detail_view, name='match_detail_view')`
2. Сохранить `path('match-preview/', views.match_preview, name='match_preview')` для демо (первый матч)
3. Новая view `match_detail_view(request, match_id)`:
   - Вызвать `get_match_detail(match_id)`
   - Если матч не найден → 404
   - Контекст: все данные для Hero (счёт, статус), player stats, team comparison, highlights
4. `match_preview` → редирект на первый `Match.objects.first()` или рендер с мок-данными если нет матчей

**Проверка**: `/match/1/` рендерит реальную страницу матча.

### 4.6 Обновить team_preview view — принять team_id

**Файл**: `tournament/views.py` + `tournament/urls.py`

**Действия**:
1. Изменить URL: `path('team-stats/<int:team_id>/', views.team_stats_view, name='team_stats_view')`
2. Сохранить `path('team-preview/', ...)` для демо
3. Новая view `team_stats_view(request, team_id)`:
   - Вызвать `get_team_detail(team_id)`
   - Контекст: roster, match history, team stats

**Проверка**: `/team-stats/1/` рендерит реальные данные команды.

### 4.7 Обновить player_preview view — принять player_id

**Файл**: `tournament/views.py` + `tournament/urls.py`

**Действия**:
1. Изменить URL: `path('player/<int:player_id>/', views.player_detail_view, name='player_detail_view')`
2. Сохранить `path('player-preview/', ...)` для демо
3. Новая view `player_detail_view(request, player_id)`:
   - Вызвать `get_player_detail(player_id)`
   - Контекст: profile, match log, stats, ranks

**Проверка**: `/player/1/` рендерит реальные данные игрока.

### 4.8 Удалить или пометить как deprecated _sports_demo_bundle()

**Файл**: `tournament/views.py`

**Действия**:
1. НЕ удалять `_sports_demo_bundle()` пока, но:
   - Обернуть в `# ─── DEMO DATA (remove after DB migration) ─── `
   - Добавить в начало `import warnings; warnings.warn("Using mock data", DeprecationWarning)`
2. preview views должны использовать её только как fallback когда БД пуста

**Проверка**: При наличии seed data — mock не используется. При пустой БД — страницы рендерятся.

---

## ФАЗА 5: ФРОНТЕНД — TOURNAMENT HUB

### 5.1 Починить standings toggle (Groups / Overall)

**Файл**: `tournament/templates/tournament/tournament_preview.html`

**Действия**:
1. Убедиться что data-view-toggle="standings" установлен на обоих кнопках
2. Убедиться что data-view-panel="standings" data-view="groups" на контейнере групп
3. Убедиться что data-view-panel="standings" data-view="overall" на контейнере overall
4. Проверить что `sports-preview.js` toggle-логика работает (класс `is-hidden`)
5. При загрузке: groups видимый, overall скрытый

**Проверка**: Клик на "Overall" скрывает группы и показывает общую таблицу. Клик на "Groups" — обратно.

### 5.2 Доработать schedule grid — визуальное улучшение

**Файл**: `tournament/templates/tournament/tournament_preview.html` + `static/css/sports-preview.css`

**Действия**:
1. Каждый time slot должен показывать:
   - Время слева (крупно, моноширинный шрифт)
   - Stage label (GROUP A, QUARTER-FINAL, SEMI-FINAL 1–4, FINAL и т.д.)
   - 1–3 карточки матчей (по количеству кортов в этом слоте)
2. Каждая карточка матча:
   - Номер корта (Court 1 / Court 2 / Court 3)
   - Team A name vs Team B name
   - Счёт по сетам (если матч завершён)
   - Статус бейдж (Scheduled / Live / Finished)
   - Кликабельно → переход на `/match/<id>/`
3. Добавить CSS для `.sp-court-match`:
   - Финальные матчи (stage=FINAL) — золотой акцент `--sp-orange`
   - Текущий LIVE матч — пульсирующая рамка `--sp-cyan`
   - FINISHED — приглушённый стиль

**Проверка**: Расписание показывает все 28 матчей, сгруппированные по 8 временным слотам.

### 5.3 Добавить Highlights секцию

**Файл**: `tournament/templates/tournament/tournament_preview.html`

**Действия**:
1. Секция `#highlights` уже есть — проверить что шаблон рендерит `highlights` из контекста
2. Каждый highlight — `.sp-highlight-card`:
   - Thumbnail (если есть media_url) или placeholder
   - Заголовок
   - Описание (truncate 100 chars)
3. Grid: 3 колонки desktop, 1 колонка mobile

**Проверка**: 3–5 highlight card рендерятся корректно.

### 5.4 Добавить ссылки навигации на странице хаба

**Файл**: `tournament/templates/tournament/tournament_preview.html`

**Действия**:
1. Entity nav (`.sp-entity-nav`) должен содержать ссылки:
   - Tournament Hub (активная)
   - Teams → `/teams-preview/`
   - Dream Team → `/dream-team-preview/`
   - Match Centre → `/match-preview/`
2. Каждая ссылка кликабельна и работает
3. Текущая страница отмечена классом `is-active`

**Проверка**: Все навигационные ссылки работают, переходят на правильные страницы.

### 5.5 Hero секция хаба — финализация

**Файл**: `tournament/templates/tournament/tournament_preview.html`

**Действия**:
1. Hero содержит:
   - Заголовок турнира (i18n)
   - Подзаголовок с датой и местом
   - CTA кнопки: "View Schedule" (scroll to #matches), "See Teams" (→ teams page)
2. Убрать любые оставшиеся мок-метрики (team count, match count) из Hero
3. Убедиться что background — спортивный визуал (gradient + noise)

**Проверка**: Hero чистый, без числовых метрик, с 2 CTA.

---

## ФАЗА 6: ФРОНТЕНД — СТРАНИЦА МАТЧА

### 6.1 Проверить и доработать шаблон match page

**Файл**: найти шаблон для `match_preview` (возможно inline в views.py или отдельный файл)

**Действия**:
1. Если шаблон не найден — найти его через grep по 'match_preview' или 'match-preview' в templates
2. Если inline в views — вынести в отдельный файл `tournament/templates/tournament/match_detail.html`
3. Структура шаблона должна содержать:

**БЛОК A — Hero (Scoreboard)**:
- Флаг/логотип Team A | Счёт | Флаг/логотип Team B
- Set scores под основным счётом (e.g., 25:20 | 22:25 | 15:11)
- Статус матча (badge)
- Название этапа (e.g., "Semi-Final 1–4")
- Время и корт

**БЛОК B — Team Comparison**:
- Side-by-side bars для: Kills, Aces, Blocks, Pass %, Attack Eff%
- Team A значение | Bar | Team B значение
- Цвета: Team A = cyan, Team B = orange

**БЛОК C — Player Stats Table**:
- Toggle: Team A / Team B / All
- Таблица с колонками: # | Name | Pos | Kills | Aces | Blocks | Pts | Att Eff% | Pass%
- Сортировка по клику на заголовок
- На mobile: карточки вместо таблицы

**БЛОК D — Highlights**:
- Список highlight записей для этого матча

**Проверка**: Все 4 блока рендерятся. Пустые блоки показывают fallback "No data yet".

### 6.2 Добавить JavaScript сортировку таблицы статистики

**Файл**: `static/js/sports-preview.js` (расширить)

**Действия**:
1. Добавить функцию `initTableSort()`:
   - Найти все таблицы с классом `.sp-player-table`
   - На каждый `<th>` с атрибутом `data-sort-key` повесить click handler
   - Сортировать `<tbody>` rows по содержимому соответствующего `<td>`
   - Поддержать числовую сортировку (kills, aces) и строковую (name)
   - Toggle direction: asc → desc → asc
   - Визуальный индикатор: ▲/▼ в заголовке
2. Вызвать `initTableSort()` в IIFE после инициализации toggle system

**Проверка**: Клик по "Kills" сортирует таблицу по kills descending. Повторный клик — ascending.

### 6.3 Добавить toggle Team A / Team B / All для player stats

**Файл**: `static/js/sports-preview.js` + шаблон match_detail.html

**Действия**:
1. В шаблоне: добавить `.sp-toggle-row` с 3 кнопками:
   - `data-view-toggle="match-stats"` `data-view="team-a"` — Team A name
   - `data-view-toggle="match-stats"` `data-view="team-b"` — Team B name
   - `data-view-toggle="match-stats"` `data-view="all"` — All
2. Два/Три panel для `data-view-panel="match-stats"`:
   - `data-view="team-a"` — таблица Team A
   - `data-view="team-b"` — таблица Team B
   - `data-view="all"` — объединённая таблица
3. JS уже поддерживает toggle через `data-view-toggle` / `data-view-panel` — ничего добавлять не нужно

**Проверка**: Переключение работает. Default — "All" активен.

### 6.4 Responsive cards on mobile для player stats

**Файл**: `static/css/sports-preview.css`

**Действия**:
1. На viewport < 768px:
   - Скрыть `.sp-player-table` (`display: none`)
   - Показать `.sp-player-cards` (mobile карточки)
2. Каждая карточка `.sp-player-card`:
   - Номер и имя сверху
   - Позиция badge
   - Grid 2×3 со stat values (Kills, Aces, Blocks, Pts, Att Eff, Pass%)
3. На desktop > 768px — карточки скрыты, таблица видна

**Проверка**: Resize окна < 768px → карточки. > 768px → таблица.

### 6.5 Добавить навигацию к предыдущему/следующему матчу

**Файл**: шаблон match_detail.html + view

**Действия**:
1. В view передавать `prev_match_id` и `next_match_id`:
   ```python
   prev_match = Match.objects.filter(match_number__lt=match.match_number).order_by('-match_number').first()
   next_match = Match.objects.filter(match_number__gt=match.match_number).order_by('match_number').first()
   ```
2. В шаблоне: стрелки ← Match 5 | Match 7 → внизу Hero или сверху

**Проверка**: Навигация переходит на корректные матчи. На первом/последнем — одна стрелка скрыта.

---

## ФАЗА 7: ФРОНТЕНД — СТРАНИЦА КОМАНДЫ

### 7.1 Проверить и доработать шаблон team page

**Файл**: найти шаблон для `team_preview`

**Действия**:
1. Структура:

**БЛОК A — Hero**:
- Название команды (крупно)
- Город + Лига level badge
- Группа (e.g., "Group B")

**БЛОК B — Roster**:
- Grid карточек игроков
- Каждая карточка: #Номер | Имя Фамилия | Позиция | Кликабельно → /player/<id>/
- Капитан помечен badge "C"

**БЛОК C — Match History**:
- Список матчей команды (из Match.objects.filter(Q(team_a=team)|Q(team_b=team)))
- Каждый ряд: Stage | Opponent | Score | Result (W/L) | → link to match
- Кликабельно на матч

**БЛОК D — Team Stats Summary**:
- Агрегированные stats за весь турнир:
  - Total Kills, Aces, Blocks, Points Won
  - Attack Efficiency (средняя)
  - Win/Loss record

**Проверка**: Все 4 блока рендерятся с реальными данными.

### 7.2 Связать roster cards с player pages

**Файл**: шаблон team page

**Действия**:
1. Каждый игрок — `<a href="{% url 'player_detail_view' player.id %}">`
2. Hover: подсветка карточки (glow effect из CSS)

**Проверка**: Клик на игрока переводит на его страницу.

---

## ФАЗА 8: ФРОНТЕНД — СТРАНИЦА ИГРОКА

### 8.1 Проверить и доработать шаблон player page

**Файл**: найти шаблон для `player_preview`

**Действия**:
1. Структура:

**БЛОК A — Profile Hero**:
- Имя и фамилия (крупно)
- #Номер | Позиция badge | Команда (ссылка на team page)

**БЛОК B — Match Log**:
- Таблица: date/time | Opponent | Kills | Aces | Blocks | Pts | Att Eff
- Каждая строка — один матч (ссылка на match page)
- Последняя строка — TOTAL / AVERAGE

**БЛОК C — Stat Cards**:
- 6 карточек: Points Won, Kills, Aces, Blocks, Attack Eff%, Pass 3%
- Каждая карточка: значение + rank position ("3rd best")

**БЛОК D — Awards**:
- MVP selections (если есть)
- Dream Team entries (если есть)
- Category leader positions

**Проверка**: Все блоки рендерятся. Пустые awards показывают fallback.

### 8.2 Rank calculation в player data service

**Файл**: `tournament/sports_data.py`

**Действия**:
1. В `get_player_detail()` для каждой stat категории:
   - Посчитать rank данного игрока среди всех игроков турнира
   - Формат: `{'value': 42, 'rank': 3, 'total': 84}` — "3rd of 84 players"
2. Категории для rank: points_won, kills, aces, blocks, attack_efficiency, pass_3_pct

**Проверка**: Rank корректен — самый высокий kills = rank 1.

---

## ФАЗА 9: ФРОНТЕНД — DREAM TEAM PAGE

### 9.1 Доработать визуализацию площадки

**Файл**: `tournament/templates/tournament/dream_team_preview.html` + `static/css/sports-preview.css`

**Действия**:
1. Площадка `.sp-court`:
   - Зелёный фон с линиями волейбольной площадки (CSS borders)
   - Сетка `.sp-court__net` разделяет площадку
   - 7 позиций с абсолютным позиционированием
2. Каждая позиция `.sp-court-player`:
   - Круглый аватар/иконка с номером
   - Позиция label (OH, MB, S, OPP, L)
   - Имя игрока
   - Команда
   - Ключевая метрика (e.g., "14 kills", "8 aces")
3. Анимация: при загрузке игроки "появляются" с задержкой (GSAP stagger)
4. Responsive: на mobile площадка скроллится горизонтально или перестраивается в список

**Проверка**: 7 позиций видны на площадке. На mobile читабельно.

### 9.2 Добавить category leaders под площадкой

**Файл**: `dream_team_preview.html`

**Действия**:
1. Под площадкой секция "Category Leaders":
   - Top Scorer: лучший по points_won
   - Best Server: лучший по ace % (мин. порог попыток)
   - Best Receiver: лучший по 3-pass % (мин. порог)
   - Best Blocker: лучший по blocks
   - Best Setter: лучший по assists
2. Каждый лидер — `.sp-award-list` item с #, именем, командой, значением
3. Данные передаются из view

**Проверка**: 5 категорий лидеров видны под площадкой.

---

## ФАЗА 10: TEAMS LIST PAGE

### 10.1 Усилить teams_preview

**Файл**: `tournament/templates/tournament/teams_preview.html`

**Действия**:
1. Каждая группа — карточка с таблицей:
   - Group A / B / C / D header
   - Строки: rank | team name | city | record (W-L) | pts
2. Каждое имя команды — ссылка на `/team-stats/<id>/`
3. Добавить toggle "Grid / Table" (grid = текущие карточки, table = плоская таблица всех 12)

**Проверка**: Все 12 команд видны. Ссылки работают.

---

## ФАЗА 11: I18N — ЛОКАЛИЗАЦИЯ

### 11.1 Проверить и добавить все i18n ключи для новых шаблонов

**Файл**: `static/js/navbar.js`

**Действия**:
1. Пройти по каждому шаблону и проверить что КАЖДЫЙ текстовый элемент имеет `data-i18n`:
   - `tournament_preview.html`: standings headers, schedule labels, highlight titles
   - `teams_preview.html`: page title, group headers, column headers
   - `dream_team_preview.html`: page title, position labels, category leader labels
   - `match_detail.html`: hero labels, stat column headers, toggle buttons
   - `team_stats.html`: section headers, stat labels
   - `player_detail.html`: profile fields, stat labels, match log headers
2. Для каждого нового `data-i18n` ключа — добавить перевод в `T.en` и `T.pl`

**ПОЛНЫЙ СПИСОК КЛЮЧЕЙ ДЛЯ ПРОВЕРКИ** (минимум):

**Tournament Hub** (`sports_hub.*`):
- `sports_hub.title` — "Tournament Hub" / "Hub Turniejowy"
- `sports_hub.standings` — "Standings" / "Tabela"
- `sports_hub.schedule` — "Schedule" / "Harmonogram"
- `sports_hub.highlights` — "Highlights" / "Najlepsze Momenty"
- `sports_hub.groups` — "Groups" / "Grupy"
- `sports_hub.overall` — "Overall" / "Ogólna"
- `sports_hub.col_rank` — "#"
- `sports_hub.col_team` — "Team" / "Drużyna"
- `sports_hub.col_played` — "P" / "M"
- `sports_hub.col_wins` — "W" / "W"
- `sports_hub.col_losses` — "L" / "P"
- `sports_hub.col_sets` — "Sets" / "Sety"
- `sports_hub.col_points` — "Pts" / "Pkt"
- `sports_hub.court_label` — "Court" / "Boisko"
- `sports_hub.time_label` — "Time" / "Czas"
- `sports_hub.view_match` — "View Match" / "Zobacz Mecz"

**Match Page** (`match_page.*`):
- `match_page.title` — "Match Details" / "Szczegóły Meczu"
- `match_page.sets` — "Sets" / "Sety"
- `match_page.team_comparison` — "Team Comparison" / "Porównanie Drużyn"
- `match_page.player_stats` — "Player Statistics" / "Statystyki Zawodników"
- `match_page.all_players` — "All" / "Wszyscy"
- `match_page.kills` — "Kills" / "Ataki"
- `match_page.aces` — "Aces" / "Asy"
- `match_page.blocks` — "Blocks" / "Bloki"
- `match_page.points` — "Points" / "Punkty"
- `match_page.att_eff` — "Att Eff%" / "Ef. Ataku%"
- `match_page.pass_pct` — "Pass%" / "Przyjęcie%"
- `match_page.assists` — "Assists" / "Asysty"
- `match_page.position` — "Pos" / "Poz"
- `match_page.no_data` — "Statistics not yet available" / "Statystyki jeszcze niedostępne"

**Team Page** (`team_page.*`):
- `team_page.roster` — "Roster" / "Skład"
- `team_page.match_history` — "Match History" / "Historia Meczów"
- `team_page.team_stats` — "Team Statistics" / "Statystyki Drużyny"
- `team_page.captain` — "Captain" / "Kapitan"
- `team_page.opponent` — "Opponent" / "Przeciwnik"
- `team_page.result` — "Result" / "Wynik"

**Player Page** (`player_page.*`):
- `player_page.profile` — "Player Profile" / "Profil Zawodnika"
- `player_page.match_log` — "Match Log" / "Log Meczowy"
- `player_page.stats` — "Statistics" / "Statystyki"
- `player_page.awards` — "Awards" / "Nagrody"
- `player_page.total` — "Total" / "Suma"
- `player_page.average` — "Average" / "Średnia"
- `player_page.rank` — "Rank" / "Pozycja"

**Dream Team** (`dream_team_page.*`):
- `dream_team_page.title` — "Dream Team" / "Drużyna Marzeń"
- `dream_team_page.category_leaders` — "Category Leaders" / "Liderzy Kategorii"
- `dream_team_page.top_scorer` — "Top Scorer" / "Najlepszy Punktujący"
- `dream_team_page.best_server` — "Best Server" / "Najlepszy Serwujący"
- `dream_team_page.best_receiver` — "Best Receiver" / "Najlepszy Przyjmujący"
- `dream_team_page.best_blocker` — "Best Blocker" / "Najlepszy Blokujący"
- `dream_team_page.best_setter` — "Best Setter" / "Najlepsza Rozgrywająca"

**Teams List** (`teams_list_page.*`):
- `teams_list_page.title` — "All Teams" / "Wszystkie Drużyny"
- `teams_list_page.record` — "Record" / "Bilans"

**Проверка**: Переключение EN/PL на каждой странице — все тексты переводятся. Нет оставшихся английских текстов при PL режиме.

### 11.2 Добавить i18n для статусов и этапов

**Файл**: `static/js/navbar.js`

**Действия**:
1. Статусы:
   - `status.scheduled` — "Scheduled" / "Zaplanowany"
   - `status.live` — "LIVE" / "NA ŻYWO"
   - `status.finished` — "Finished" / "Zakończony"
2. Этапы:
   - `stage.group` — "Group" / "Grupa"
   - `stage.qf` — "Quarter-Final" / "Ćwierćfinał"
   - `stage.sf` — "Semi-Final" / "Półfinał"
   - `stage.final` — "Final" / "Finał"
   - `stage.place_N` — "Nth Place" / "N. Miejsce"

**Проверка**: Все динамические тексты переведены.

---

## ФАЗА 12: ВИЗУАЛЬНАЯ ПОЛИРОВКА

### 12.1 Scoreboard стиль для Hero матча

**Файл**: `static/css/sports-preview.css`

**Действия**:
1. Активировать и доработать существующий `.sp-scoreboard`:
   - Тёмный фон с clip-path corners
   - Team A слева (cyan accent) | Score центр (крупно, 72px+) | Team B справа (orange accent)
   - Set scores под основным счётом в ряд
   - Status badge (LIVE = пульс, FINISHED = статичный)
2. На mobile: вертикальный layout (Team A сверху, Score, Team B снизу)

**Проверка**: Scoreboard выглядит как ТВ-графика для спортивных трансляций.

### 12.2 Анимации GSAP для всех новых секций

**Файл**: `static/js/sports-preview.js`

**Действия**:
1. Убедиться что новые секции имеют класс `.sp-reveal`:
   - Match hero scoreboard
   - Player stats table rows
   - Team comparison bars
   - Dream team player positions
   - Award list items
2. GSAP уже настроен в IIFE — новые элементы подхватятся автоматически через `.sp-reveal`
3. Для Dream Team: специальная анимация — игроки появляются по одному на площадке с delay 0.2s

**Проверка**: При прокрутке до секции — элементы анимированно появляются. С prefers-reduced-motion — мгновенно.

### 12.3 Comparison bars для Team vs Team

**Файл**: `static/css/sports-preview.css`

**Действия**:
1. Стиль `.sp-comparison-bar`:
   - Контейнер: горизонтальная полоса 100% ширины
   - Левая часть (Team A) = cyan, ширина пропорциональна значению
   - Правая часть (Team B) = orange
   - Значения по обе стороны (Team A value | bar | Team B value)
   - Label по центру ("Kills", "Aces", etc.)
2. 5–7 полос в секции team comparison

**Проверка**: При значениях 40 vs 35 — левая часть занимает ~53%, правая ~47%.

### 12.4 Status badges

**Файл**: `static/css/sports-preview.css`

**Действия**:
1. `.sp-status-badge`:
   - Base: pill-shape, 12px text, uppercase, letter-spacing
   - `--scheduled`: серый фон, белый текст
   - `--live`: красный фон с pulse анимацией + белая точка перед текстом
   - `--finished`: зелёный фон, checkmark
2. Использовать в: schedule grid, match hero, match history

**Проверка**: 3 визуально различных badge.

### 12.5 Mobile responsive проверка и фиксы

**Файл**: `static/css/sports-preview.css`

**Действия**:
1. Breakpoints:
   - `>= 1024px` — full desktop (3-column grids, wide tables)
   - `768px–1023px` — tablet (2-column grids, tables scroll horizontally)
   - `< 768px` — mobile (1-column, cards instead of tables)
2. Проверить каждый шаблон:
   - `tournament_preview.html`: schedule slots → 1 колонка на mobile
   - `match_detail.html`: scoreboard → vertical, table → cards
   - `team_stats.html`: roster → 2 колонки, stats → 1 колонка
   - `player_detail.html`: stat cards → 2 колонки, match log → cards
   - `dream_team_preview.html`: court → горизонтальный scroll или list fallback
   - `teams_preview.html`: groups → 1 колонка
3. Добавить `@media (max-width: 767px)` правила для каждого компонента

**Проверка**: Chrome DevTools → iPhone 12 Pro → все страницы читаемы, ничего не обрезано.

### 12.6 Перепроверить clip-path и glass-morphism consistency

**Файл**: `static/css/sports-preview.css`

**Действия**:
1. Все `.sp-card` элементы должны использовать одинаковый clip-path:
   ```css
   clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 14px 100%, 0 calc(100% - 14px));
   ```
2. Все card backgrounds: `var(--sp-surface)` с `backdrop-filter: blur(6px)`
3. Border: `1px solid var(--sp-border)`
4. Hover: `border-color: var(--sp-cyan)`

**Проверка**: Визуальная однородность всех карточек на всех страницах.

---

## ФАЗА 13: SEO И МЕТАДАННЫЕ

### 13.1 Добавить meta tags для всех спортивных страниц

**Файл**: каждый шаблон в `{% block extra_head %}`

**Действия**:
1. Для каждой страницы в `{% block extra_head %}`:
   ```html
   <title>{{ page_title }} — Pocket Aces Tournament</title>
   <meta name="description" content="{{ page_description }}">
   <link rel="canonical" href="{{ request.build_absolute_uri }}">
   ```
2. Views должны передавать `page_title` и `page_description`:
   - Tournament Hub: "Tournament Hub — Pocket Aces Volleyball"
   - Match: "Match 5: Team A vs Team B — Pocket Aces"
   - Team: "Team Name — Pocket Aces Tournament"
   - Player: "John Doe #10 — Pocket Aces Tournament"
   - Dream Team: "Dream Team — Pocket Aces Tournament"
   - Teams: "All Teams — Pocket Aces Tournament"

**Проверка**: Каждая страница имеет уникальный `<title>` и `<meta description>`.

### 13.2 Open Graph tags для social sharing

**Файл**: каждый шаблон в `{% block extra_head %}`

**Действия**:
1. Добавить:
   ```html
   <meta property="og:title" content="{{ page_title }}">
   <meta property="og:description" content="{{ page_description }}">
   <meta property="og:type" content="website">
   <meta property="og:url" content="{{ request.build_absolute_uri }}">
   ```
2. Для match page: `og:type="article"` 

**Проверка**: При вставке URL в мессенджер — показывается preview с правильным title.

---

## ФАЗА 14: A11Y И PERFORMANCE

### 14.1 Базовая доступность

**Файл**: все шаблоны

**Действия**:
1. Все интерактивные элементы (`<a>`, `<button>`) имеют:
   - Видимый focus ring (`:focus-visible`)
   - `aria-label` где текст не очевиден
2. Все таблицы имеют `<thead>` с `scope="col"`
3. Все изображения имеют `alt`
4. Навигационные tabs имеют `role="tablist"`, `role="tab"`, `aria-selected`
5. Toggle buttons имеют `aria-pressed`
6. Цветовой контраст ≥ 4.5:1 для текста (WCAG AA)

**Проверка**: Tab-навигация по странице проходит все интерактивные элементы без пропусков.

### 14.2 prefers-reduced-motion

**Файл**: `static/css/sports-preview.css` + `static/js/sports-preview.js`

**Действия**:
1. CSS: все `@keyframes` анимации обёрнуты в:
   ```css
   @media (prefers-reduced-motion: no-preference) {
     /* animations */
   }
   ```
2. JS: GSAP проверка уже есть — убедиться что она работает:
   ```js
   if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
     // GSAP animations
   }
   ```
3. Pulse на LIVE badge — тоже отключается при reduced-motion

**Проверка**: Включить reduced-motion в OS → никаких анимаций на странице.

### 14.3 Performance baseline

**Файл**: все шаблоны + CSS

**Действия**:
1. Убедиться что все CSS файлы загружаются в `<head>` (уже так)
2. Убедиться что JS файлы загружаются с `defer` или в конце `<body>` (уже так в base.html)
3. Изображения: использовать `loading="lazy"` для всех `<img>` ниже fold
4. Минимизировать количество DOM-элементов на страницах с большими таблицами
5. Убедиться что GSAP animations не блокируют рендер

**Проверка**: DevTools → Lighthouse → Performance score ≥ 80 на desktop.

---

## ФАЗА 15: ССЫЛКИ И НАВИГАЦИЯ

### 15.1 Cross-page navigation consistency

**Файл**: все шаблоны

**Действия**:
1. Из **Tournament Hub**:
   - Standings: team name → `/team-stats/<id>/`
   - Schedule: match card → `/match/<id>/`
   - Entity nav → teams, dream team
2. Из **Match Page**:
   - Team names → `/team-stats/<id>/`
   - Player names (в таблице) → `/player/<id>/`
   - Prev/Next match
   - Back to hub
3. Из **Team Page**:
   - Roster player → `/player/<id>/`
   - Match history match → `/match/<id>/`
   - Back to teams list
4. Из **Player Page**:
   - Team name → `/team-stats/<id>/`
   - Match log match → `/match/<id>/`
   - Back to team
5. Из **Dream Team Page**:
   - Player name → `/player/<id>/`
   - Team name → `/team-stats/<id>/`
   - Back to hub
6. Из **Teams List**:
   - Team name → `/team-stats/<id>/`
   - Back to hub

**Проверка**: Можно пройти по всем путям без dead links: Hub → Match → Player → Team → Hub.

### 15.2 Update base.html navigation

**Файл**: `tournament/templates/base.html`

**Действия**:
1. Navbar "Match Centre" ссылка → `/tournament-preview/`
2. Проверить что mobile burger menu содержит те же ссылки
3. Footer navigation: добавить "Match Centre" если нет

**Проверка**: Навигация из header работает на desktop и mobile.

---

## ФАЗА 16: ТЕСТИРОВАНИЕ

### 16.1 Создать unit tests для моделей

**Файл**: `tournament/tests.py`

**Действия**:
1. `TestMatch`:
   - Создание матча с двумя командами
   - `winner` property возвращает правильную команду
   - `is_finished` = True когда status = FINISHED
2. `TestPlayerMatchStats`:
   - `points_won` = kills + aces + blocks
   - `attack_efficiency` корректна
   - `attack_efficiency` = None при 0 попытках
   - `ace_pct` корректна
3. `TestGroupStanding`:
   - Правильная сортировка по points

**Проверка**: `python manage.py test tournament` — все тесты проходят.

### 16.2 Создать tests для CSV import

**Файл**: `tournament/tests.py`

**Действия**:
1. Фикстуры: создать 2 команды с по 6 игроков, 1 матч
2. `test_parse_valid_csv` — корректный CSV → 0 ошибок, 12 rows
3. `test_parse_csv_missing_columns` — CSV без обязательных колонок → errors
4. `test_parse_csv_invalid_numbers` — отрицательные числа → errors
5. `test_preview_no_commit` — preview не меняет БД
6. `test_confirm_creates_stats` — confirm создаёт PlayerMatchStats
7. `test_confirm_overwrites` — повторный import перезаписывает данные
8. `test_recalculate_standings` — standings корректны после импорта

**Проверка**: `python manage.py test tournament.tests` — все тесты зелёные.

### 16.3 Создать smoke tests для views

**Файл**: `tournament/tests.py`

**Действия**:
1. Для каждого URL:
   - GET запрос → status 200
   - Response содержит ожидаемый HTML элемент
   - При пустой БД → 200 с fallback контентом (не 500)
2. URLs:
   - `/tournament-preview/`
   - `/teams-preview/`
   - `/dream-team-preview/`
   - `/match-preview/`
   - `/team-preview/`
   - `/player-preview/`
   - `/match/1/` (с seed data)
   - `/team-stats/1/` (с seed data)
   - `/player/1/` (с seed data)

**Проверка**: Все 9 URL → 200.

---

## ФАЗА 17: QA CHECKLIST

### 17.1 Smoke test checklist (ручная проверка)

Выполнить после каждого деплоя. Каждый пункт — отдельное действие:

1. [ ] Открыть Tournament Hub — страница загружается < 5 сек
2. [ ] Standings: Groups вид показывает 4 группы × 3 команды
3. [ ] Standings: Overall вид показывает 12 команд отсортированных
4. [ ] Toggle Groups ↔ Overall работает
5. [ ] Schedule показывает 28 матчей в 8 временных слотах
6. [ ] Schedule: 3 корта видны параллельно в слоте
7. [ ] Клик на матч в schedule → открывает match page
8. [ ] Match page: scoreboard показывает score
9. [ ] Match page: Team A / Team B toggle работает
10. [ ] Match page: Player stats таблица сортируется по клику
11. [ ] Match page: prev/next навигация работает
12. [ ] Player name в таблице → кликабелен → открывает player page
13. [ ] Player page: match log показывает матчи
14. [ ] Player page: stat cards показывают значения
15. [ ] Team name → кликабелен → открывает team page
16. [ ] Team page: roster показывает игроков
17. [ ] Team page: match history показывает результаты
18. [ ] Dream Team: площадка показывает 7 позиций
19. [ ] Dream Team: category leaders под площадкой
20. [ ] Teams List: 4 группы, все команды кликабельны
21. [ ] EN/PL toggle работает на каждой странице
22. [ ] Mobile (< 768px): таблицы → карточки
23. [ ] Mobile: навигация через burger menu
24. [ ] CSV Import: загрузить тестовый CSV → preview работает
25. [ ] CSV Import: confirm → данные появляются на странице
26. [ ] CSV Import: повторный import → данные перезаписаны

---

## ПОРЯДОК ВЫПОЛНЕНИЯ (зависимости)

```
ФАЗА 1 (Модели)
  └── ФАЗА 2 (CSV Import) 
  │     └── ФАЗА 3 (Seed Data)
  │           └── ФАЗА 4 (Views с БД)
  │                 ├── ФАЗА 5 (Hub frontend)
  │                 ├── ФАЗА 6 (Match page)
  │                 ├── ФАЗА 7 (Team page)
  │                 ├── ФАЗА 8 (Player page)
  │                 ├── ФАЗА 9 (Dream Team page)
  │                 └── ФАЗА 10 (Teams List page)
  │                       └── ФАЗА 11 (i18n)
  │                             └── ФАЗА 12 (Visual polish)
  │                                   ├── ФАЗА 13 (SEO)
  │                                   ├── ФАЗА 14 (A11y + Perf)
  │                                   └── ФАЗА 15 (Navigation)
  │                                         └── ФАЗА 16 (Tests)
  │                                               └── ФАЗА 17 (QA)
```

Фазы 5–10 могут выполняться параллельно после завершения Фазы 4.
Фазы 13–15 могут выполняться параллельно после завершения Фазы 12.

---

## ПРИМЕЧАНИЯ ДЛЯ ИИ-АГЕНТА

1. **Не удаляй мок-данные** из `_sports_demo_bundle()` до завершения Фазы 4.4.8. Они нужны как fallback.
2. **Всегда проверяй** `python manage.py check` после изменения моделей.
3. **Используй** `@transaction.atomic` для всех операций записи в БД.
4. **Не кеширй** derived stats (attack_efficiency и т.д.) в БД — считай на лету.
5. **CSS переменные** — используй `--sp-*` из sports-preview.css. НЕ хардкодь цвета.
6. **i18n** — каждый текст через `data-i18n`. НЕ хардкодь строки в шаблонах.
7. **GSAP** — используй класс `.sp-reveal` для автоматической анимации при скролле.
8. **Testing**: запускай `python manage.py test tournament` после каждой фазы.
9. **Миграции**: не используй `--merge` без необходимости. Миграции должны быть линейными.
10. **Время** HH:mm, timezone Europe/Warsaw — всегда явно.
