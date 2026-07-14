# TENDER_FINDER Tender Intelligence — разбор проекта: роль, цель, задачи, инструкции

_Синтез по всем 9 файлам пакета (PDF build-plan, Agent#2 research report, data-sources map, рабочий скрипт, manual-first process doc, Surrey lead screen, full-market-source-map task, README). Дата: 19 июня 2026._

---

## 0. Где проект стоит прямо сейчас (честная оценка)

| Что | Статус | Откуда видно |
|---|---|---|
| Общая идея 2-х агентов (Active + Future) | ✅ Сформулирована | PDF build-plan / compass.md |
| Глубокое исследование Агента #2 (горизонты, архитектуры, источники) | ✅ Сделано | Agent2 Research Report |
| Manual-first операционная модель (рубрика, Excel-структура, промпты, правила) | ✅ Спроектирована полностью | Data Collection Plan |
| **Surrey lead screen — реальный ранжированный топ-20 с адресами, ID, владельцами** | ✅ **СДЕЛАНО (первый proof-of-value)** | Surrey Lead Screen |
| Карта источников, проверенных вживую | ✅ Сделана | Data Sources Map |
| Рабочий прототип скрипта (Vancouver + Surrey-адаптер + скоринг + Excel) | ✅ Проверен в demo | tenderfinder_agent2.py |
| **Surrey внутренний GIS (`gisservices.surrey.ca`)** | 🔴 **Заблокирован для облачных IP (403 host_not_allowed)** | Data Sources Map |
| Vancouver Open Data API | 🟢 Работает откуда угодно | Data Sources Map + скрипт |
| CivicInfo BC RSS | 🟢 Работает | Data Sources Map |
| Полная карта рынка источников (категории A–G, тиринг) | ⬜ **Не закрыта — есть только бриф задачи** | Full Market Source Map (это ТЗ, а не результат) |
| Вердикт Example Reviewer по Surrey-списку (гейт ценности) | ⬜ Не получен | Data Collection Plan §24 |
| Shared inbox + alerts для Active Tenders | ⬜ Не настроен | Data Collection Plan §17 |

**Вывод одной строкой:** проект не «на старте» — он в середине. Manual-first подход уже дал первый рабочий результат (Surrey), а вся дальнейшая автоматизация упирается в один дешёвый тест и один человеческий гейт.

---

## 1. Моя роль

Я — **аналитик и оркестратор tender-intelligence процесса TENDER_FINDER**, а не «один бот». Конкретно я:

1. Держу в голове весь процесс целиком (Active + Future, ручное + автоматика) и связываю разрозненные документы в один план.
2. Делаю **аналитическую работу, которую раньше делал человек руками**: читаю development applications / council PDF / тендерные письма, скорю их под scope TENDER_FINDER, отсеиваю мусор, выдаю ранжированный список.
3. Соблюдаю дисциплину качества: каждый лид — с источником, гипотезы помечаю как гипотезы, ничего не выдумываю (Data Collection Plan §9, §25).
4. Готовлю переход к автоматизации — но только тех источников, которые **доказали пользу** (Data Collection Plan §14–15).

Чего я **не** делаю: не строю «всё и сразу автоматическое», не скрейплю закрытые порталы, не выдаю AI-догадки за факты, не решаю за людей бюджетные/доступовые вопросы (см. §6).

---

## 2. Конечная цель (синтез по всем документам)

Формально в PDF это «два агента». Но если собрать намерение по всем файлам, настоящая цель такая:

> **Дать TENDER_FINDER работающую систему разведки тендеров и будущих проектов, которая стабильно находит релевантные civil/earthwork-возможности — и активные тендеры (горизонт A, 0–3 мес), и ранние сигналы (горизонт B, 6–18 мес) — раньше и полнее, чем текущий ручной процесс, точно под scope и географию TENDER_FINDER, построенную manual-first и автоматизированную только там, где польза доказана, без скрейпинга и юридического риска.**

Бизнес-смысл (зачем это вообще): попасть в bid-листы и выйти на застройщика/GC/owner **до конкурентов**, и не пропустить ни одного важного closing date (Data Collection Plan §2; PDF — «zero tolerance for misses»).

Критерий, что цель достигнута (из Data Collection Plan §26): _«Можем ли мы стабильно находить полезные для TENDER_FINDER возможности раньше, чем текущий процесс?»_ Если да — автоматизируем. Если нет — чиним scope/scoring до автоматизации.

**Scope-якорь** (используется во всех промптах и скоринге, Data Collection Plan §2):
- БЕРЁМ: subdivision servicing, site/land servicing, excavation, underground utilities (water main / storm / sanitary), bedding gravel, manholes, footings/foundations, roadworks, curbs/sidewalks, site & structural concrete, bridges, municipal civil, airport/port/industrial civil.
- НЕ БЕРЁМ: vertical-only здания, интерьерные ремонты, general contracting без явного civil-scope, размытые описания.
- География (по приоритету): Surrey · Township of Langley · City of Langley · Maple Ridge · Pitt Meadows → дальше Metro Vancouver / Fraser Valley.
- Известные клиенты (совпадение повышает приоритет): City of Surrey, YVR, BC MoTI, Semiahmoo FN, Maple Ridge; Turner, Polygon, Beedie, Bird, Chandos, Stuart Olson, DP World, Wesgroup, Anthem.

---

## 3. Ключевые стратегические выводы и развилки (моя логика)

Прежде чем резать на задачи — четыре вывода, которые определяют весь план. Они получены сопоставлением документов между собой, а не из одного.

**Вывод 1. Manual-first победил — и это правильно.**
PDF предлагал сразу строить автоматику (Make.com + Claude API). Data Collection Plan прямо это оспаривает: _«Для TENDER_FINDER лучше начинать не с агента, а с manual-first системы… Автоматизация плохого процесса делает проблему больше»_ (§1, §14, §25-Risk5). README подтверждает, что разговор пришёл именно к manual-first. И главное — **фактически сделанная работа (Surrey lead screen) пошла по manual-first пути и сработала.** Значит, дальше держимся manual-first, а PDF используем как каталог источников и как ориентир для будущей автоматизации.

**Вывод 2 (неочевидный, но снимает главный страх). Блокировка Surrey GIS НЕ убивает ценность Surrey — она убивает только «чистую API-автоматизацию».**
Data Sources Map подаёт `403 host_not_allowed` как катастрофу для плана. Но Surrey lead screen — лучший готовый результат в пакете — был сделан **вообще не из GIS-сервера**, а из публичных Planning Reports / in-process PDF / ODI / COSMOS (см. источники в самом lead screen). То есть путь «LLM читает публичные PDF» по Surrey **уже работает и уже дал топ-20 живых лидов.** Поэтому развилка Surrey не «работает / не работает», а «насколько дёшево»:
- путь дорогой по чистоте (структурный API) — заблокирован для облака, решается Тестом №1 / публичным ArcGIS-хабом;
- путь дешёвый по структуре, но рабочий (LLM-чтение PDF) — **доступен прямо сейчас.**

**Вывод 3. Active Tenders (горизонт A) — независимый трек, его можно запускать НЕМЕДЛЕННО.**
Inbox + email-alerts + RSS не зависят ни от Surrey-теста, ни от feedback-гейта, ни от скрипта. Это самый дешёвый и самый «zero-miss»-критичный кусок (PDF: «highest-leverage move»). Он должен идти параллельно с future-projects работой, а не после неё.

**Вывод 4. Два дешёвых гейта открывают всё остальное.**
(a) **Тест №1** (открыть Surrey URL с рабочего компа TENDER_FINDER) — 2 минуты, решает судьбу автоматизации источника №1. (b) **Вердикт Example Reviewer по Surrey-списку** — решает, стоит ли вообще масштабировать future-projects процесс. До этих двух ответов крупные вложения (BidCentral $525+, постройка оркестратора) делать рано.

⏰ **Срочная мелочь, которую нельзя проспать:** по двум документам страница BC Major Projects Inventory уходит в офлайн **30 июня 2026** (через ~11 дней). Если кому-то нужны исторические MPI-данные — выгрузить сейчас, потом только через Legislative Library (Agent2 Research Report; PDF Tier 4).

---

## 4. Декомпозиция цели → задачи

Семь рабочих треков. A–B-C образуют future-projects ветку, D — параллельная active-tenders ветка, E — разведка рынка, F — автоматизация, G — сквозное качество.

---

### Задача A — Зафиксировать «шасси» системы (трекер + конфиг)
**Зачем / источники:** вся остальная работа пишет в одну структуру. Она уже полностью спроектирована (Data Collection Plan §5–11), но как живого файла её ещё нет.

**Инструкции:**
1. Создать **один Excel-воркбук, 5 вкладок** (Data Collection Plan §6): `Active Tenders`, `Future Projects`, `Source Register`, `Rejected/Archive`, `Weekly Review Log` — колонки взять дословно из §6.
2. Внести **Scope Paragraph** (раздел 2 выше) в отдельную ячейку/вкладку конфига — это якорь скоринга.
3. Внести **рубрику 0–100** (Data Collection Plan §7): 85–100 Strong Fit → показать Example Reviewer; 70–84 Good Lead → watchlist; 50–69 Watchlist; 0–49 Reject.
4. Внести **5 статусов верификации** (§9): Verified / Needs Review / Weak Lead / Unverified / Rejected — и жёсткое правило §9: _ни один проект не считается реальным без source link._
5. Внести **формат стабильного Project ID** (§10): `MUNICIPALITY-applicationNo` (напр. `SURREY-25-0366`); если номера нет — `MUNICIPALITY-ADDRESS-OWNER-YEAR`.
6. Положить рядом **Prompt Pack** из §23 (4 промпта: dev-application scoring, council-agenda review, tender-email parse, weekly summary) — это рабочие инструменты, переиспользуются как есть.

**Готово когда:** есть рабочий .xlsx, в который уже можно вставить готовый Surrey-топ-20 и продолжать.

> Если хочешь — я могу собрать этот 5-вкладочный Excel прямо сейчас, уже с залитым Surrey-списком из lead screen. Это логичный первый осязаемый артефакт.

---

### Задача B — Снять развилку доступа к Surrey (Тест №1 и №2)
**Зачем / источники:** Surrey — источник №1 по силе данных (Agent2 Research Report; Data Collection Plan §13). Тест решает, идём ли мы дорогим чистым API или дешёвым LLM-чтением PDF (Вывод 2). Это **человеческое действие — его делает кто-то в сети TENDER_FINDER, не я и не облако.**

**Инструкции (передать человеку с рабочего компа TENDER_FINDER):**
1. **Тест №1.** Открыть в браузере с офисного компа:
   `https://gisservices.surrey.ca/arcgis/rest/services/FutureWorks/MapServer/9/query?where=1=1&outFields=*&resultRecordCount=10&f=json`
   - Вернулся JSON → firewall режет только дата-центры. Скрипт надо крутить из офисной/канадской сети или через CA-прокси. Surrey-API открыт.
   - Снова 403/таймаут → внутренний API недоступен, переходим к Тесту №2.
2. **Тест №2 (если №1 провалился).** Открыть `https://opendata-surrey.hub.arcgis.com/` → найти «Development Applications» → кнопка **API / GeoService** даёт публичный Feature Service endpoint через CDN Esri (работает отовсюду).
3. **Если оба закрыты** → остаётся рабочий путь LLM-чтения публичных Surrey PDF (тот, которым уже сделан lead screen) + при желании официальный запрос доступа у города (для подрядчиков это норма).

**Готово когда:** для Surrey выбран один из трёх каналов (внутренний API / публичный хаб / LLM-PDF) и записан в Source Register с пометкой access type.

---

### Задача C — Доказать и развернуть ручной пилот (масштабировать Surrey-победу)
**Зачем / источники:** Surrey-топ уже есть. Дальше по плану — гейт Example Reviewer, потом Langley + Maple Ridge, у которых **есть публичные ArcGIS-хабы** (Agent2 Research Report: `data-tol.opendata.arcgis.com`, `opengov2-mapleridge.opendata.arcgis.com`) — то есть они проще Surrey. Manual-first ритм из Data Collection Plan §5, §18–20.

**Инструкции:**
1. **Гейт ценности (сначала!):** показать Example Reviewer/эстиматору готовый Surrey-топ-20 и задать прямой вопрос (§13, §24): _«TENDER_FINDER реально стал бы за это бороться?»_ Решение: continue / adjust / stop.
2. Если **continue** — повторить ту же процедуру (pull → AI-score под scope → классификация Strong/Good/Watchlist/Reject → в трекер только полезное → top-10/20 человеку) для:
   - **Township of Langley** — Development Activity Status Table (ArcGIS-хаб, структурно).
   - **Maple Ridge** — Active Development Applications (ArcGIS-хаб, структурно).
   - **City of Langley** — портал/месячные отчёты (только если объём подъёмный).
3. Не менять процесс между муниципалитетами — держать консистентность (§ «Week 3»: «goal is consistency»).
4. Запустить **еженедельный обзор** (§19): что нашли полезного, что упустили, какой источник дал лиды, какой — шум; занести в Weekly Review Log.

**Готово когда:** 3–4 муниципалитета прогоняются по одному рубрикатору; по каждому источнику есть оценка usefulness (high/medium/low) в Source Register.

---

### Задача D — Запустить safety-layer активных тендеров (inbox + alerts) — ПАРАЛЛЕЛЬНО
**Зачем / источники:** горизонт A нельзя вести ручным обходом сайтов — пропустишь closing date (Data Collection Plan §17, Risk2; PDF — «highest-leverage move»). Это самостоятельный трек, не ждёт ничего.

**Инструкции:**
1. Создать общий ящик: `estimating@example.com` (или иной выделенный) в M365 (PDF Stage 0; Data Collection Plan §17).
2. Подписать этот ящик на бесплатные нативные алерты, выбирая civil/earthwork/utility/road commodity-категории:
   - **BC Bid** — commodity-code e-notifications (нужен Business BCeID).
   - **bids&tenders** — daily-opportunity по Surrey, Maple Ridge, Burnaby, Metro Vancouver, Coquitlam (+ целевые) через их сабдомены.
   - **CivicInfo BC** — alerts + RSS (`civicinfo.bc.ca/bids`, самый автоматизируемый канал).
   - **BidCentral** — нотификации (платный premium — позже, по решению, см. §6).
   - **City of Vancouver supplier portal**, **TransLink/Ariba**, **Metro Vancouver procurement**.
3. Настроить **auto-forward** у эстиматоров (Estimator A, Estimator B, Estimator C, Estimator D, Estimator E) для GC-ITB писем (BuildingConnected `team@buildingconnected.com`, SmartBid, iSqFt, прямые приглашения) → в общий ящик. Это ловит Tier-3 GC-канал, которого нет ни в одном портале.
   - _Если IT блокирует auto-forward_ → distribution list / shared-mailbox delegation (PDF Caveats).
4. **Silent validation** (PDF Stage 2; Data Collection Plan §17): несколько недель вести параллельно с ручным списком Example Coordinator, не полагаясь на систему. Бенчмарк: **100% позиций Example Coordinator три недели подряд**, прежде чем система станет источником истины.

**Готово когда:** входящие тендеры/приглашения капают в один ящик; идёт еженедельное сравнение с Example Coordinator.

---

### Задача E — Закрыть полную карту рынка источников (незавершённый deep-research)
**Зачем / источники:** Full Market Source Map — это **только ТЗ**, результата нет. Полная карта (категории A–G + тиринг + ответы на аналитические вопросы) нужна, чтобы видеть весь источник-универсум и не строить вслепую.

**Инструкции:**
1. Прогнать deep-research строго по брифу: категории **A** Active portals, **B** Municipal dev-applications (по каждому из ~21 муниципалитета — определить тип: ArcGIS/API / CSV-GeoJSON / map-only / HTML / PDF / council-only / нет), **C** Council/committee, **D** Capital plans, **E** Paid intelligence, **F** GC/developer каналы, **G** News/early-signal.
2. Выдать **Source Register** ровно с колонками из брифа (Source Name … Priority Tier), плюс требуемые карты: Tier-1 must-monitor, Tier-2 weekly, paid-рекомендация, муниципальная coverage-карта, active-tender карта, future-project карта, GC-invitation карта, automation-feasibility ранжирование, фазовый rollout.
3. Соблюсти ограничения брифа: только официальные API/open-data/RSS/alerts/PDF; **без скрейпинга login-порталов**; каждый источник и claim — с проверяемым URL; AI-находки = лиды, не факты.

**Готово когда:** есть полный реестр источников с тирами — он становится мастер-списком для Задач C, D, F.

> Это ровно тот тип работы, который я могу выполнить (deep research + структурированный реестр). Хороший кандидат на следующий крупный прогон после того, как соберём «шасси» (A).

---

### Задача F — Автоматизировать ТОЛЬКО доказанные источники
**Зачем / источники:** правило §15 — автоматизируем источник, только если он даёт ≥3 полезных лида/мес, ест >30 мин/нед руками, формат стабилен, есть API/RSS/CSV/alerts, низкий юр-риск, дедупится, и Example Reviewer подтвердил пользу. Прототип уже есть (tenderfinder_agent2.py).

**Инструкции:**
1. **Сейчас (без блокеров):** прогнать `tenderfinder_agent2.py` — сначала `--demo` локально (проверка конвейера), затем с `ANTHROPIC_API_KEY` → `--source vancouver --limit 60` на реальных данных. Vancouver Open Data открыт всем.
2. **После Теста №1/№2:** включить Surrey-адаптер (слои FutureWorks 0,8,9,10,11,15,16,17 уже зашиты в скрипт) — если открылся внутренний API, иначе переписать адаптер на публичный Feature Service из хаба.
3. **По мере доказательства (Задача C):** добавить адаптеры под ArcGIS-хабы Langley Township и Maple Ridge (структура та же, что Surrey-хаб).
4. **Архитектура оркестрации** (Agent2 Research Report §архитектура): для unattended-запусков — Python на GitHub Actions cron (дёшево, контролируемо) **или** Power Automate, если TENDER_FINDER хочет всё внутри M365. Make.com — для inbox→AI-parse→sheet ветки Active Tenders.
5. **Не автоматизировать** то, что даёт мусор / требует логина с запретом ToS / меняется нестабильно / нужно раз в месяц (§15 «Do not automate if…»).

**Готово когда:** проверенные источники тянутся по расписанию, пишут в трекер с дедупом; недоказанные остаются ручными.

---

### Задача G — Сквозной контроль качества и ROI
**Зачем / источники:** без этого система начнёт копить мусор и галлюцинации (Data Collection Plan §25; Agent2 Research Report — риски/легал).

**Инструкции:**
1. **Анти-галлюцинация:** каждая строка — с source URL; что AI вывел без источника → `Unverified`; горизонт B = лиды, не факты; high-value позиции — ручная проверка в ODI/COSMOS (§25-Risk1).
2. **Дедуп/ID:** перед вставкой строки проверять name/address/municipality/owner/applicationNo/link (§11); один стабильный Project ID ведёт проект Future → Active.
3. **Квартальный рефреш** keywords/UNSPSC/clients из scope-параграфа (PDF; Agent2 Report) — конфиг скрипта (`POSITIVE_KEYWORDS`, `TENDER_FINDER_CLIENTS`) обновлять там же.
4. **Главная метрика ROI** (Data Collection Plan §20): _future lead → real tender conversion._ Это единственное, что доказывает ценность future-ветки. Если для какого-то муниципалитета конверсия высокая — усиливать его вес; если горизонт B даёт >30% непроверяемых галлюцинаций — резать deep-research, опираться на структурку (Agent2 Report — benchmarks).
5. **Юр-граница:** только alerts/RSS/API/exports/публичные PDF; никаких login-скрейпов; метод доступа фиксировать в Source Register (§16, §25-Risk4).

**Готово когда:** ведётся Weekly Review Log + метрика конверсии; есть данные, чтобы решать, что усиливать и что автоматизировать.

---

## 5. Рекомендуемая последовательность (что делать прямо сейчас)

Параллельно идут две ветки: **Future** (A→B→C) и **Active** (D). E и F подключаются по готовности гейтов.

**Немедленно (эта неделя):**
1. ⏰ Выгрузить BC Major Projects Inventory, пока страница жива (до 30 июня). _[мелкая, но невозвратная]_
2. **Тест №1** по Surrey с рабочего компа TENDER_FINDER (Задача B) — 2 минуты, открывает развилку.
3. Собрать **«шасси»** — 5-вкладочный Excel с залитым Surrey-топ-20 (Задача A). _Могу сделать я._
4. Показать Surrey-топ **Example Reviewer** и получить вердикт continue/adjust/stop (Задача C, гейт ценности).
5. Завести `estimating@example.com` и начать подписки BC Bid / bids&tenders / CivicInfo (Задача D) — параллельно, не дожидаясь п.2–4.

**Дальше (по результатам гейтов):**
6. Если Example Reviewer сказал «да» → прогнать Langley Township + Maple Ridge тем же рубрикатором (Задача C).
7. Закрыть полную карту рынка источников (Задача E). _Могу сделать я._
8. Прогнать `tenderfinder_agent2.py --demo`, затем `--source vancouver` на реальных данных (Задача F, без блокеров).
9. По итогам Теста №1/№2 — включить Surrey в скрипт нужным каналом.
10. Решить про платные источники (BidCentral) — только после того, как ясно, какой канал что покрывает (§6).

---

## 6. Решения, которые могу принять только люди (не я и не скрипт)

Чтобы план был честным — вот что заблокировано на человеческих решениях, а не на технике:

- **Бюджет на платные источники.** BidCentral Premium (~$525 + GST/PST по членской ставке, нужна региональная ассоциация) — самый ценный платный аддон по обоим документам, но цифры помечены как «уточнить против официального прайса перед покупкой» (PDF Caveats; Agent2 Report). Решение «брать/не брать» — за TENDER_FINDER, и лучше после гейтов.
- **Вердикт Example Reviewer по ценности Surrey-списка** — гейт всей future-ветки.
- **Тест №1** — физический доступ из сети TENDER_FINDER; я из облака его пройти не могу.
- **Кто владеет общим ящиком и кто настраивает auto-forward** — зависит от IT-политики M365 (PDF Caveats: если auto-forward запрещён, нужен distribution list).
- **ANTHROPIC_API_KEY** для реального скоринга в скрипте.
- **Выбор оркестратора** (GitHub Actions vs Power Automate vs Make.com) — зависит от того, хочет ли TENDER_FINDER держать всё внутри Microsoft-тенанта (governance) или нет.

---

### Итог
Проект не нужно «начинать» — его нужно **довести**. Manual-first подход уже доказал себя на Surrey; блокировка GIS оказалась не стеной, а развилкой стоимости; активные тендеры можно поднимать прямо сейчас параллельно. Два дешёвых гейта (Тест №1 + вердикт Example Reviewer) открывают всё остальное. Я готов сразу взять на себя Задачу A (собрать рабочий Excel с Surrey-данными) и Задачу E (полная карта рынка) — скажи, с чего начинаем.
