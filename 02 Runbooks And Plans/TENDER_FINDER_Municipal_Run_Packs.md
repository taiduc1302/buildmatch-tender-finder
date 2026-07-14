# TENDER_FINDER — пакеты прогона по муниципалитетам (ready-to-run)

_Поверх очищенного Source_Register. Каждый «прогон» = один муниципалитет, один проход по единому рубрикатору (Prompt v2), результат — в `Future_Projects`. Дата: 22 июня 2026._

Порядок прогонов и статусы продублированы во вкладке **Run_Queue** воркбука v5. Surrey уже прогнан (20 лидов загружены). Следующие на очереди — **Township of Langley** и **Maple Ridge** (оба структурные ArcGIS-хабы, ядро географии TENDER_FINDER).

---

## 0. Единая процедура прогона (одинакова для всех муниципалитетов)

Дисциплина консистентности: процесс между муниципалитетами **не меняем** — меняется только источник и строчка географии в промпте.

1. **Pull** — вытащить активные development applications из источника муниципалитета (способ — в пакете ниже: ArcGIS REST `/query`, Hub download API, или LLM-чтение HTML/PDF).
2. **Score** — прогнать записи через **Prompt v2** (вкладка `Prompt_Pack`, строка 1), заменив строку географии на нужный муниципалитет (см. §0.1).
3. **Classify** — по баллу: ≥85 Strong Fit · 70–84 Good Lead · 50–69 Watchlist · <50 Reject.
4. **Dedup** — нормализовать по `address + applicationNo`; один проект из нескольких записей (rezoning/subdivision/DP) = одна строка.
5. **Write** — занести в `Future_Projects` по схеме (см. §0.2): Project ID = `<MUNI>-<appno>`, Verification = **Needs Review**, обязательный source URL, баллы по весам v2.
6. **Hand-off** — top-10/20 показать Example Reviewer; по top-10 — обязательный **ручной второй проход** (открыть полный отчёт/PDF, вытащить owner/applicant/agent/civil-consultant, сверить стадию). Это отделяет lead-identification (автоматизируемо) от tender-timing (нельзя без ручной проверки).

### 0.1 Строка географии для Prompt v2 (подставлять под каждый прогон)
> `GEOGRAPHY RULE: Use <MUNICIPALITY> public data ONLY for this task. TENDER_FINDER's wider service area is company context only — do NOT pull other municipalities into this screen.`

Полный текст Prompt v2 — во вкладке `Prompt_Pack`, ряд 1 (веса: Civil 35 / Type 25 / Stage 20 / Location 10 / Owner 10).

### 0.2 Куда писать (схема `Future_Projects`, 21 колонка)
`Project ID | Date Found | Source | Source URL | Project Title | Owner/Developer | Municipality | Application No | Application Type/Stage | Scope Summary | Expected Civil Component | Fit Score | Fit Class (формула — не трогать) | Verification Status | Est. Civil Timeline/Horizon | Est. Value | Next Milestone | Linked Active Tender ID | Assigned To | Notes | Last Updated`

---

## 1. ДЕТАЛЬНЫЕ ПАКЕТЫ — запускать сейчас

### 1A. Township of Langley  🟢 самый чистый источник
- **Что:** Development Activity Status Table (все заявки + стадия), ArcGIS Hub.
- **Hub-страница:** `https://data-tol.opendata.arcgis.com/datasets/development-activity-status-table`
- **Item ID (слой):** `aea97e65c9db4dad8242783c96e6b70c_1`
- **Pull, вариант A (download API, без поиска GUID):**
  `https://data-tol.opendata.arcgis.com/api/download/v1/items/aea97e65c9db4dad8242783c96e6b70c/geojson?layers=1`
- **Pull, вариант B (FeatureServer /query):** на Hub-странице → кнопка **«I want to use this» / «View API Resources»** → скопировать **GeoService (FeatureServer) URL** → добавить:
  `/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=2000`
- **Поля:** имена полей посмотреть в ответе `f=json` или на вкладке Data датасета; смэппить applicationNo / type / status-stage / address / applicant / description / dates → схема §0.2.
- **Карта (визуальная проверка):** GeoSource `https://geosource.tol.ca`.
- **Промпт:** v2, география = `Township of Langley`.
- **Feasibility:** High. Структурно проще Surrey — лучший кандидат на первый авто-адаптер после Surrey.

### 1B. Maple Ridge
- **Что:** Active Development Applications (rezoning / DP / subdivision) **со стадией процесса** — то есть готовый future-signal.
- **Hub-страница:** `https://opengov2-mapleridge.opendata.arcgis.com/datasets/active-development-applications`
- **Pull, вариант A (FeatureServer /query):** Hub-страница → **«I want to use this»** → GeoService URL → `/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=2000`.
- **Pull, вариант B (download API):** на странице взять item ID → `…/api/download/v1/items/<itemId>/geojson?layers=0`.
- **Поля:** смэппить как в 1A (есть поле стадии — оно ценно для Est. Timeline/Horizon).
- **Промпт:** v2, география = `Maple Ridge`.
- **Feasibility:** High. Тот же адаптер-паттерн, что TOL — писать оба адаптера одной функцией.

> После прогона 1A+1B у тебя будет 3 ядровых муниципалитета в `Future_Projects` (Surrey+TOL+MR) на одном рубрикаторе — этого хватает, чтобы у Example Reviewer была полная картина core-географии, и чтобы решить, какие источники идут в авто-скрипт первыми.

---

## 2. ЯДРОВЫЕ ВТОРИЧНЫЕ ПАКЕТЫ — после 1A/1B

### 2A. City of Langley
- **Что:** список активных заявок (type/applicant/contact) + месячный Development Activity PDF. Малый объём, чисто.
- **Источники:** `langleycity.ca` DA Portal + open-data `https://data-langleycity.opendata.arcgis.com`.
- **Pull:** LLM-чтение HTML-списка + месячный PDF (структурного API по заявкам мало — объём позволяет читать).
- **Промпт:** v2, география = `City of Langley`. **Feasibility:** Medium.

### 2B. Pitt Meadows
- **Что:** структурной таблицы нет. Сигнал — Council agendas + страница Current Developments. Индустриальные сигналы: **Golden Ears Business Park**, Eagle Meadows, Katzie FN.
- **Источники:** `pittmeadows.ca/business-development/current-developments` + council agendas; Meadows Mapview (только зонирование).
- **Pull:** LLM-чтение страницы + agendas (ручной). **Промпт:** v2, география = `Pitt Meadows`. **Feasibility:** Low (manual).

---

## 3. ШИРЕ / FRASER VALLEY — очередь (после того как core доказан)

Запускать той же процедурой §0. Для большинства — сначала подтвердить, что dev-app слой открыт (а не только map-only).

| # | Муниципалитет | Источник / endpoint | Способ | Feasibility | Примечание |
|---|---|---|---|---|---|
| 6 | **Abbotsford** | `opendata-abbotsford.hub.arcgis.com` | ArcGIS REST `/query` | High | Крупнейший рынок FV. Подтвердить dev-app слой. |
| 7 | **Coquitlam** | `data.coquitlam.ca` + Dev Info Portal (experience.arcgis.com) | ArcGIS REST `/query`; проверить open vs map-only | High | Структурный портал PROJ ##-###. |
| 8 | **Delta** | `delta.ca` current apps + DeltaMap | ArcGIS REST `/query` или LLM-чтение | Medium | Порт/индустрия (DP World), Tilbury/Roberts Bank. |
| 9 | **New Westminster** | `opendata.newwestcity.ca` | ArcGIS REST `/query` (permits подтверждены) | Medium | Dev-app может быть HTML/council. |
| 10 | **Burnaby** | `data.burnaby.ca` + BurnabyMap | Open-data pull; подтвердить feature service | Med-High | Capital-works + land-dev tracker. |
| 11 | **Richmond** | `richmond.ca/…/currentdevapps.htm` + RIM map | LLM-чтение HTML «Dev Apps in Process» | Medium | Рядом с YVR. |
| 12 | **Chilliwack** | `chilliwack.com` (maps / open data) | Verify endpoint → API или LLM | Medium | Платформа inferred; рост FV. |
| 13 | **Mission** | `mission.ca` | Verify; вероятно council + map | Low-Med | Платформа inferred. |

---

## 4. TIER 3 / РУЧНЫЕ — низкий приоритет, проверить endpoint

| Муниципалитет | Источник | Способ | Примечание |
|---|---|---|---|
| North Vancouver (City) | `cnv.org` | Verify endpoint | Map+open data inferred. |
| North Vancouver (District) | `geoweb.dnv.org` | Download SHP/KML или LLM | Esri GEOweb. |
| West Vancouver / White Rock / Port Moody | `westvancouver.ca` · `whiterockcity.ca` · `portmoody.ca` | Council agendas (ручной) | Малый объём, map/council-only. |
| Малые villages (×4) | сайты муниципалитетов | Council-only (ручной) | Только при явном civil-сигнале. |

---

## 5. OWNER / CAPITAL-каналы — ОТДЕЛЬНЫЙ трек (не dev-app прогон)

Это не development-applications — здесь читаются капитальные планы, поэтому **другой промпт** (Prompt 2 — Council / Capital review), а не v2.

- **Metro Vancouver — Capital:** `metrovancouver.org/services/liquid-waste/procurement`. Прямой owner: water/wastewater (Iona Island WWTP, 15-летний). → Prompt 2.
- **BC MoTI / TransLink — Capital:** `gov.bc.ca` (MoTI) + `translink.ca/plans-and-projects`. Surrey-Langley SkyTrain, Pattullo, мосты, Major Road Network. MoTI — известный клиент TENDER_FINDER; его тендеры идут через BC Bid. → Prompt 2.
- **Surrey FutureWorks layers:** `gisservices.surrey.ca` (internal, **403 для облака**). 🔒 **Сначала Тест №1 с рабочего компа TENDER_FINDER** — он решает, открывается ли API из офисной сети. Слои: Sanitary / Storm / Water / Roads / Drainage (planned works). До теста — не трогать.

---

### Что готово к запуску прямо сейчас
**Township of Langley** и **Maple Ridge** — полностью (реальные endpoint'ы, паттерн запроса, маппинг, промпт). Дальше — City of Langley и Pitt Meadows. Шире/FV и tier-3 — в очереди, по той же процедуре §0. Owner-каналы (Metro Van, MoTI/TransLink, Surrey FutureWorks) — отдельным треком и под другим промптом; Surrey FutureWorks ждёт Тест №1.

Если нужно — следующим ходом могу **выполнить прогон TOL или Maple Ridge** (вытащить данные с их хабов, прогнать через v2, загрузить результат в `Future_Projects` рядом с Surrey), либо дописать в `tenderfinder_agent2.py` адаптеры под эти два хаба.
