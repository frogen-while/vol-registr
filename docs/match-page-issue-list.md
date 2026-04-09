# Match Page: Issue List

Ниже список задач в формате, близком к GitHub Issues / Jira tickets.

## MP-01. Спроектировать матчевые модели и миграции

Type: Backend
Priority: P0
Labels: backend, data-model, migrations
Depends on: none

Description:
- Добавить или актуализировать сущности матчевого контура для Match-раздела.
- Покрыть этапы турнира, матчи, статистику игроков, Dream Team, MVP и highlights.

Scope:
- Stage
- Match
- PlayerMatchStats
- MatchStatSnapshot или аналог агрегатов
- DreamTeamEntry
- MVPSelection
- MatchHighlight

Acceptance Criteria:
- Миграции создаются без конфликтов.
- Миграции применяются локально.
- Сущности доступны в Django admin.
- Match связан с Team и этапом турнира.

## MP-02. Реализовать preview CSV перед импортом

Type: Backend
Priority: P0
Labels: backend, import, csv
Depends on: MP-01

Description:
- Реализовать безопасный предпросмотр CSV без записи в базу.
- Показать ошибки формата, пропущенные поля и потенциальные конфликты.

Acceptance Criteria:
- Есть endpoint предпросмотра.
- Возвращается нормализованный preview-результат.
- Ошибки формата выводятся в человекочитаемом виде.
- Импорт не коммитит данные на этапе preview.

## MP-03. Реализовать подтвержденный импорт CSV с полной перезаписью матча

Type: Backend
Priority: P0
Labels: backend, import, overwrite
Depends on: MP-01, MP-02

Description:
- Реализовать коммит импорта после preview.
- При повторной загрузке того же матча полностью перезаписывать статистику.
- При частичном CSV публиковать доступные данные и помечать пропуски.

Acceptance Criteria:
- Есть confirm-import endpoint.
- Повторный импорт заменяет предыдущую статистику матча.
- Неполные данные не ломают публикацию.
- Пропущенные поля видны как partial data.

## MP-04. Поднять публичный API расписания и Match hub данных

Type: Backend
Priority: P0
Labels: backend, api, public
Depends on: MP-01

Description:
- Подготовить API для Hero и расписания по этапам.
- Поддержать 3 параллельных матча и 24-часовой формат времени.

Acceptance Criteria:
- Endpoint возвращает матчи по этапам.
- Формат времени соответствует HH:mm.
- Таймзона Europe/Warsaw передается явно.
- Данные пригодны для табов Match 1/2/3.

## MP-05. Поднять публичный API статистики игроков и рейтингов

Type: Backend
Priority: P0
Labels: backend, api, stats
Depends on: MP-01, MP-03

Description:
- Отдать детальную статистику игроков после импорта.
- Поддержать фильтры и сортировку.
- Отдать позиционные рейтинги и Dream Team.

Acceptance Criteria:
- Работают фильтры: team, position, stage, match.
- Работает сортировка по ключевым колонкам.
- Возвращаются Dream Team и позиционные рейтинги.
- Возвращаются MVP матча и турнира.

## MP-06. Поднять API и права для ручной правки MVP, Dream Team и highlights

Type: Backend
Priority: P1
Labels: backend, admin, permissions
Depends on: MP-01, MP-05

Description:
- Реализовать ручную корректировку curated-блоков.
- Доступ только супер-админу.

Acceptance Criteria:
- Только супер-админ может редактировать MVP.
- Только супер-админ может редактировать Dream Team.
- Только супер-админ может редактировать highlights.

## MP-07. Добавить публичный route и шаблон Match hub preview/V1

Type: Frontend
Priority: P0
Labels: frontend, django-template, public-page
Depends on: MP-04

Description:
- Создать публичную Match-страницу в существующем визуальном языке сайта.
- Добавить Hero, счет/статус, табы параллельных матчей и доминантный блок расписания этапа.

Acceptance Criteria:
- Страница доступна по отдельному публичному route.
- Hero показывает счет и статус.
- Есть табы Match 1/2/3.
- Блок расписания визуально доминирует после Hero.

## MP-08. Реализовать fallback без стрима как основной сценарий

Type: Frontend
Priority: P0
Labels: frontend, fallback, stream
Depends on: MP-07

Description:
- Так как трансляция не гарантирована, страница должна полноценно работать без плеера.
- Если стрима нет, вместо него выводить fallback на расписание ближайших матчей.
- Если стрим есть, показывать его в Hero под счетом.

Acceptance Criteria:
- При отсутствии стрима интерфейс не ломается.
- При отсутствии стрима показывается fallback-блок.
- При наличии стрима плеер можно встроить в Hero через feature flag.
- Если стрим недоступен, показывается сообщение и кнопка refresh.

## MP-09. Собрать UI статистики игроков с фильтрами, сортировкой и infinite scroll

Type: Frontend
Priority: P0
Labels: frontend, stats, ux
Depends on: MP-05, MP-07

Description:
- Собрать главный статистический блок страницы.
- На desktop использовать плотный аналитический layout.
- На mobile перейти на карточки игроков.

Acceptance Criteria:
- На desktop доступны фильтры и сортировка.
- На mobile используются карточки игроков.
- Длинные списки грузятся через infinite scroll.
- Частичные данные отображаются корректно.

## MP-10. Собрать UI Dream Team, MVP и highlights

Type: Frontend
Priority: P0
Labels: frontend, rankings, content
Depends on: MP-05

Description:
- Отрисовать топ-3 по каждой позиции.
- Добавить отдельные блоки MVP матча и MVP турнира.
- Добавить топ-10 highlights.

Acceptance Criteria:
- Dream Team выводится по позициям.
- MVP match и MVP tournament вынесены в отдельные блоки.
- Highlights top-10 отображаются отдельной секцией.

## MP-11. Добавить публичную страницу игрока

Type: Frontend
Priority: P1
Labels: frontend, player-page, seo
Depends on: MP-05

Description:
- Реализовать отдельную публичную страницу игрока.
- Страница должна быть SEO-friendly и связана с Match hub.

Acceptance Criteria:
- Из таблиц и карточек можно перейти на страницу игрока.
- Страница игрока индексируема.
- На странице выводятся имя, номер, команда, позиция и статистика.

## MP-12. Добавить публичную детальную Match-страницу и архив во вкладке Match

Type: Frontend
Priority: P1
Labels: frontend, match-page, archive
Depends on: MP-04, MP-05

Description:
- Реализовать детальную Match-страницу.
- Добавить архив матчей как отдельную вкладку внутри Match-раздела.

Acceptance Criteria:
- Матч кликабелен из расписания.
- Детальная Match-страница рендерится стабильно.
- Архив доступен как вкладка внутри Match-раздела.

## MP-13. Реализовать admin UI для CSV-импорта

Type: Admin
Priority: P0
Labels: admin, import-ui, staff
Depends on: MP-02, MP-03

Description:
- Собрать staff-интерфейс для загрузки CSV.
- Показать preview, ошибки и подтверждение перезаписи.

Acceptance Criteria:
- Админ загружает CSV через UI.
- Preview показывает разобранные данные до публикации.
- Перезапись матча требует явного подтверждения.

## MP-14. Локализация, a11y и motion-polish для новых страниц

Type: Frontend
Priority: P1
Labels: frontend, i18n, a11y, motion
Depends on: MP-07, MP-09, MP-10, MP-11, MP-12

Description:
- Добавить EN/PL для новых match/player экранов.
- Поддержать базовую доступность.
- Учесть prefers-reduced-motion при сохранении спортивной визуальной подачи.

Acceptance Criteria:
- Новые экраны переключаются между EN и PL.
- Базовая клавиатурная навигация работает.
- Контраст критичных блоков достаточен.
- При prefers-reduced-motion тяжелые анимации упрощаются.

## MP-15. Подготовить SEO-метаданные для Match и Player страниц

Type: Frontend
Priority: P1
Labels: frontend, seo, metadata
Depends on: MP-11, MP-12

Description:
- Подготовить title, meta description и canonical для публичных страниц.

Acceptance Criteria:
- Match-страницы индексируемы.
- Player-страницы индексируемы.
- У каждой страницы есть корректный title и meta description.

## MP-16. Провести QA smoke cycle для Sprint 1

Type: QA
Priority: P0
Labels: qa, smoke, release
Depends on: MP-03, MP-07, MP-08, MP-09, MP-10, MP-11, MP-12, MP-13

Description:
- Проверить критические сценарии Sprint 1 перед релизом.

Checklist:
- Корректный CSV импортируется.
- Ошибочный CSV показывает ошибки.
- Повторный импорт перезаписывает матч.
- Частичный CSV не ломает UI.
- Табов для 3 параллельных матчей достаточно для навигации.
- Fallback без стрима работает.
- Фильтры и сортировка статистики не ломают страницу.

Acceptance Criteria:
- Нет блокирующих дефектов P0.
- Основной post-match сценарий стабилен.

## MP-17. Проверить performance и release readiness

Type: QA
Priority: P1
Labels: qa, performance, release
Depends on: MP-14, MP-16

Description:
- Оценить загрузку на mobile 4G.
- Проверить, что визуальный слой не делает страницу непригодной.

Acceptance Criteria:
- Первичная загрузка остается в приемлемом диапазоне.
- Нет критических лагов на мобильных.
- Release readiness подтвержден для V1 без обязательного стрима.

## Рекомендуемый порядок создания issues в трекере

1. MP-01
2. MP-02
3. MP-03
4. MP-04
5. MP-05
6. MP-07
7. MP-08
8. MP-09
9. MP-10
10. MP-13
11. MP-11
12. MP-12
13. MP-14
14. MP-15
15. MP-16
16. MP-17
17. MP-06

## Смысл такого порядка

- Сначала фиксируется серверный контракт данных.
- Затем закрывается основной публичный сценарий без стрима.
- Затем подключаются detail pages, polish и QA.
- Кураторские админские правки выносятся ближе к концу, потому что они не блокируют первую рабочую V1.