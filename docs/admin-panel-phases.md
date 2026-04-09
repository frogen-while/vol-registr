# Кастомная Админ-панель — План реализации (18 фаз)

> Отдельная админка со своим тёмным минимальным дизайном (не Django Admin).
> Защита: `@staff_member_required` на всех view.
> URL-префикс: `/panel/`

---

## Что уже сделано (подготовка в предыдущих фазах)

- `Team.status` — CharField с 4 статусами (REGISTERED → AWAITING_PAYMENT → PAID → APPROVED)  
- `Team.checked_in` — BooleanField  
- `TEAM_STATUS_CHOICES` в constants.py  
- `GalleryPhoto` модель (drive_file_id, drive_url, thumbnail_url, title, order)  
- `TABLE_GALLERY_PHOTOS` в constants.py  
- CSV импорт статистики матча уже работает в Django Admin  

---

## ФАЗА 1: Каркас админки — layout, auth, роутинг

**Цель**: Базовый layout, авторизация, sidebar-навигация, пустые страницы-заглушки.

**Файлы**:
- `tournament/admin_views.py` — все view-функции кастомной админки
- `tournament/admin_urls.py` — URL-паттерны `/panel/...`
- `vol_registr/urls.py` — include admin_urls
- `tournament/templates/panel/base.html` — base layout (sidebar, topbar, content area)
- `tournament/templates/panel/login.html` — страница логина
- `static/css/panel.css` — стили админки

**Действия**:
1. Создать `admin_urls.py` с namespace `panel`, 7 URL-паттернов (dashboard, teams, schedule, stats, gallery, dreamteam, login/logout)
2. Создать `admin_views.py` с `@staff_member_required` декоратором на каждом view, заглушки `render(request, 'panel/dashboard.html')`
3. Создать `base.html` — тёмный layout: sidebar (лого, 6 пунктов меню, logout), topbar (заголовок страницы, user info), `{% block content %}`
4. Создать `login.html` — форма логина (тёмная тема)
5. Создать `panel.css` — CSS-переменные (`--panel-bg`, `--panel-surface`, `--panel-accent`), sidebar, topbar, responsive
6. Подключить `admin_urls` в `vol_registr/urls.py`

**Критерий готовности**: Переход на `/panel/` редиректит на логин → после логина видна пустая dashboard с работающим sidebar.

---

## ФАЗА 2: Dashboard — обзор статистики

**Цель**: Главная страница с KPI-карточками и сводной информацией.

**Файлы**:
- `tournament/admin_views.py` — `dashboard_view()`
- `tournament/templates/panel/dashboard.html`

**Действия**:
1. Собрать данные: кол-во команд (всего / по статусам), кол-во игроков, кол-во матчей (scheduled / finished), кол-во фото в галерее
2. Вывести 6 KPI-карточек: Teams, Players, Matches Played, Matches Remaining, Photos, Check-ins
3. Список последних 5 зарегистрированных команд
4. Список ближайших 5 матчей

**Критерий готовности**: Dashboard показывает актуальные числа из БД.

---

## ФАЗА 3: Команды — список с фильтрами

**Цель**: Таблица команд с фильтрацией и поиском.

**Файлы**:
- `tournament/admin_views.py` — `teams_list_view()`
- `tournament/templates/panel/teams_list.html`

**Действия**:
1. Таблица: Name, Group, Status, Payment, Check-in, Players count, Captain, Created
2. Фильтры: по group_name, по status, по payment_status, по checked_in
3. Поиск по имени команды / капитана
4. Сортировка по колонкам (JS или query params)

**Критерий готовности**: Список всех команд с рабочими фильтрами.

---

## ФАЗА 4: Команды — CRUD (создание, редактирование, удаление)

**Цель**: Полное управление командами через формы.

**Файлы**:
- `tournament/admin_views.py` — `team_create_view()`, `team_edit_view()`, `team_delete_view()`
- `tournament/admin_forms.py` — `AdminTeamForm`
- `tournament/templates/panel/team_form.html`
- `tournament/templates/panel/team_detail.html`

**Действия**:
1. Форма создания/редактирования команды (все поля Team + inline список игроков)
2. Детальная страница команды: все данные + список игроков + история матчей
3. Удаление с подтверждением
4. Inline-редактирование игроков (добавить/удалить/изменить)

**Критерий готовности**: Можно создать, отредактировать и удалить команду с игроками.

---

## ФАЗА 5: Команды — статусы и workflow

**Цель**: Управление статусом регистрации и batch-действия.

**Файлы**:
- `tournament/admin_views.py` — `team_status_action()`
- Обновление `teams_list.html`

**Действия**:
1. Кнопки смены статуса на детальной странице (Registered → Awaiting Payment → Paid → Approved)
2. Batch actions: выбрать несколько команд → "Mark Paid" / "Approve" / "Reset"
3. Цветные бейджи статусов в таблице (красный → жёлтый → синий → зелёный)
4. Валидация: нельзя перескочить статусы (только последовательно или назад)

**Критерий готовности**: Workflow статусов работает, бейджи отображаются корректно.

---

## ФАЗА 6: Команды — Game Day check-in

**Цель**: Быстрый чек-ин команд в день турнира.

**Файлы**:
- `tournament/admin_views.py` — `checkin_view()`, `checkin_toggle()`
- `tournament/templates/panel/checkin.html`

**Действия**:
1. Отдельная страница (или вкладка в Teams): список всех Approved команд
2. Большие чекбоксы / toggle-переключатели для каждой команды
3. AJAX-обновление (без перезагрузки страницы)
4. Прогресс-бар: X из Y команд check-in
5. Визуальное разделение: checked-in (зелёные) / not checked (серые)

**Критерий готовности**: Можно быстро отмечать check-in, состояние сохраняется мгновенно.

---

## ФАЗА 7: Расписание — список матчей

**Цель**: Просмотр всех матчей в удобном формате.

**Файлы**:
- `tournament/admin_views.py` — `schedule_list_view()`
- `tournament/templates/panel/schedule_list.html`

**Действия**:
1. Таблица матчей: #, Stage, Group, Time, Court, Team A vs Team B, Score, Status
2. Фильтры: по stage, по status, по court, по group
3. Два режима отображения: таблица и сетка по time-slot'ам (grid 3 корта × N таймслотов)
4. Цветные бейджи статуса матча (SCHEDULED / LIVE / FINISHED)

**Критерий готовности**: Все матчи из БД отображаются с фильтрами.

---

## ФАЗА 8: Расписание — создание и редактирование матчей (UI форма)

**Цель**: Создание матчей через форму.

**Файлы**:
- `tournament/admin_views.py` — `match_create_view()`, `match_edit_view()`, `match_delete_view()`
- `tournament/admin_forms.py` — `AdminMatchForm`
- `tournament/templates/panel/match_form.html`

**Действия**:
1. Форма: stage (select), group (показывать только для GROUP stage), court (select), start_time (datetime picker), team_a (select из команд), team_b (select из команд), match_number (auto или manual)
2. Валидация: team_a ≠ team_b, нет конфликта (тот же корт + то же время)
3. Редактирование: изменить любое поле + ввести счёт + изменить статус
4. Удаление с подтверждением

**Критерий готовности**: Можно создать матч через UI, счёт обновляется.

---

## ФАЗА 9: Расписание — CSV импорт расписания

**Цель**: Массовое создание матчей из CSV файла.

**Файлы**:
- `tournament/admin_views.py` — `schedule_csv_import_view()`
- `tournament/services.py` — `parse_schedule_csv()`, `import_schedule_csv()`
- `tournament/templates/panel/schedule_csv_import.html`

**Действия**:
1. Форма загрузки CSV с предпросмотром
2. Парсер CSV: колонки `Time, Team A, Team B, Group, Court` (разделитель запятая или точка с запятой)
3. Предпросмотр: таблица распарсенных матчей, подсветка ошибок (команда не найдена, конфликт времени)
4. Кнопка "Confirm Import" → создание Match объектов
5. Автоназначение `match_number` (следующие свободные)
6. Обработка ошибок: дубликаты, несуществующие команды

**Критерий готовности**: Загрузка CSV → preview → confirm → матчи созданы в БД.

---

## ФАЗА 10: Статистика — CSV импорт статистики матча

**Цель**: Перенести существующий CSV import из Django Admin в кастомную админку.

**Файлы**:
- `tournament/admin_views.py` — `stats_import_view()`
- `tournament/templates/panel/stats_import.html`

**Действия**:
1. Выбор матча из dropdown (только FINISHED или с возможностью импорта)
2. Загрузка CSV (SoloStats Live формат — уже реализован в services.py)
3. Предпросмотр: таблица игроков с распарсенными статами
4. Confirm → импорт в PlayerMatchStats + TeamMatchStats
5. Индикатор: матчи с уже импортированной статистикой
6. Использовать существующие `preview_csv_import()` и `confirm_csv_import()` из services.py

**Критерий готовности**: CSV import статистики работает в кастомной админке, аналогично Django Admin.

---

## ФАЗА 11: Статистика — просмотр и редактирование

**Цель**: Просмотр и ручное редактирование статистики матча.

**Файлы**:
- `tournament/admin_views.py` — `stats_detail_view()`, `stats_edit_view()`
- `tournament/templates/panel/stats_detail.html`
- `tournament/templates/panel/stats_edit.html`

**Действия**:
1. Список матчей с импортированной статистикой
2. Детальный просмотр: таблица PlayerMatchStats для обеих команд
3. Inline-редактирование: изменить любое поле статистики (kills, aces, blocks, etc.)
4. Пересчёт TeamMatchStats после редактирования
5. Пересчёт GroupStanding после изменения результатов

**Критерий готовности**: Можно просмотреть и отредактировать статистику любого матча.

---

## ФАЗА 12: Галерея — управление фото (Google Drive ссылки)

**Цель**: CRUD для фото (ссылки на Google Drive).

**Файлы**:
- `tournament/admin_views.py` — `gallery_list_view()`, `gallery_add_view()`, `gallery_delete_view()`
- `tournament/admin_forms.py` — `GalleryPhotoForm`
- `tournament/templates/panel/gallery.html`
- `tournament/templates/panel/gallery_form.html`

**Действия**:
1. Сетка фото с превью (thumbnail из Google Drive)
2. Форма добавления: title, Google Drive URL (парсить drive_file_id из URL), thumbnail автогенерация из Drive URL
3. Удаление фото (с подтверждением)
4. Drag-and-drop сортировка (order field)
5. Bulk-добавление: вставить несколько Google Drive ссылок сразу

**Критерий готовности**: Фото добавляются/удаляются, отображаются в сетке с превью.

---

## ФАЗА 13: Галерея — управление видео хайлайтами (Google Drive ссылки)

**Цель**: CRUD для видео (ссылки на Google Drive).

**Файлы**:
- `tournament/admin_views.py` — обновить gallery views для видео
- `tournament/models.py` — обновить `GalleryPhoto` → `GalleryItem` или добавить `GalleryVideo`
- `tournament/templates/panel/gallery.html` — вкладки Фото / Видео

**Действия**:
1. Две вкладки в галерее: Photos / Videos
2. Видео: title, Google Drive URL, описание
3. Превью видео (thumbnail или иконка)
4. CRUD аналогичный фото

**Критерий готовности**: Фото и видео управляются через 2 вкладки в одном интерфейсе.

---

## ФАЗА 14: Галерея — публичная страница на сайте

**Цель**: Страница галереи на фронтенде сайта.

**Файлы**:
- `tournament/views.py` — `gallery_view()`
- `tournament/templates/tournament/gallery.html`
- `tournament/urls.py` — новый URL `/gallery/`
- `static/css/sports-preview.css` — стили галереи
- `tournament/templates/base.html` — добавить ссылку Gallery в навигацию

**Действия**:
1. Два раздела: Фото (сетка) и Видео (карточки)
2. Lightbox для фото (клик → полноразмерное фото)
3. Видео: карточки со ссылкой на Google Drive
4. Responsive grid (3 колонки → 2 → 1)
5. Добавить "Gallery" в navbar и footer

**Критерий готовности**: Страница `/gallery/` отображает все фото и видео из БД.

---

## ФАЗА 15: Dream Team — управление

**Цель**: CRUD для Dream Team в кастомной админке.

**Файлы**:
- `tournament/admin_views.py` — `dreamteam_view()`, `dreamteam_edit_view()`
- `tournament/templates/panel/dreamteam.html`

**Действия**:
1. Визуальная площадка с 7 позициями (как на фронтенде)
2. Для каждой позиции: выбрать игрока (dropdown), metric_label, metric_value
3. Кнопка "Auto-fill" — автоматически заполнить по статистике (уже есть логика в services.py)
4. Ручная корректировка любой позиции
5. Сохранение / сброс

**Критерий готовности**: Dream Team редактируется визуально, auto-fill работает.

---

## ФАЗА 16: Миграция и адаптация существующего Django Admin

**Цель**: Обеспечить работу обоих интерфейсов без конфликтов.

**Файлы**:
- `tournament/admin.py` — обновить
- Миграция для новых полей

**Действия**:
1. Создать и применить миграцию для `Team.status`, `Team.checked_in`, `GalleryPhoto`
2. Обновить Django Admin: добавить `status`, `checked_in` в TeamAdmin list_display и list_filter
3. Зарегистрировать GalleryPhoto в Django Admin (как fallback)
4. Проверить что оба интерфейса (Django Admin + Panel) работают без конфликтов

**Критерий готовности**: `python manage.py migrate` проходит, оба интерфейса доступны.

---

## ФАЗА 17: Тестирование админки

**Цель**: Smoke-тесты для всех view кастомной админки.

**Файлы**:
- `tournament/tests.py` — добавить тесты

**Действия**:
1. Тесты авторизации: анонимный пользователь → redirect на login, staff → 200
2. Smoke-тесты каждого view: dashboard, teams_list, schedule, stats, gallery, dreamteam
3. Тесты CRUD: создание/редактирование/удаление команды
4. Тесты CSV schedule import
5. Тесты team status workflow
6. Тесты check-in toggle

**Критерий готовности**: Все тесты проходят.

---

## ФАЗА 18: QA и полировка

**Цель**: Финальная проверка, мобильная адаптация, edge cases.

**Действия**:
1. Проверить все страницы в браузере (desktop + mobile)
2. Проверить все формы: валидация, error messages
3. Проверить edge cases: пустая БД, 0 команд, 0 матчей
4. Проверить навигацию: все ссылки работают, active state в sidebar
5. Проверить responsive: sidebar collapse на мобильных
6. Проверить security: CSRF на всех формах, XSS-защита в user input
7. Performance: N+1 queries, prefetch_related

**Критерий готовности**: Админка полностью функциональна и протестирована.

---

## Зависимости между фазами

```
Фаза 1 (каркас) ──┬── Фаза 2 (dashboard)
                   ├── Фаза 3 (teams list) → Фаза 4 (CRUD) → Фаза 5 (статусы) → Фаза 6 (check-in)
                   ├── Фаза 7 (schedule list) → Фаза 8 (create match) → Фаза 9 (CSV schedule)
                   ├── Фаза 10 (CSV stats) → Фаза 11 (stats edit)
                   ├── Фаза 12 (photos) → Фаза 13 (videos) → Фаза 14 (public gallery)
                   └── Фаза 15 (dream team)

Фаза 16 (миграция) — запустить ПЕРЕД фазой 1 или сразу после
Фаза 17 (тесты) — после всех фаз
Фаза 18 (QA) — финал
```

---

## Стек и решения

| Аспект | Решение |
|--------|---------|
| UI | Кастомные HTML-шаблоны, CSS (тёмная тема), vanilla JS |
| Auth | `@staff_member_required` (Django built-in) |
| Forms | Django ModelForm + custom validation |
| AJAX | fetch API для check-in, drag-and-drop, inline edit |
| Медиа (фото) | Ссылки на Google Drive (drive_url + thumbnail_url) |
| Медиа (видео) | Ссылки на Google Drive |
| CSS | Отдельный `panel.css`, CSS custom properties, dark theme |
| Responsive | CSS Grid + media queries, sidebar collapse |
