# Карта источников данных для Agent #2 (проверено вживую, июнь 2026)

Это всё, что реально найдено и протестировано на доступность. Бери отсюда конкретные endpoint'ы.

---

## ⚠️ ГЛАВНЫЙ ВЫВОД, который меняет план

**Внутренний GIS-сервер Surrey (`gisservices.surrey.ca`) заблокирован для внешних IP.**
Ответ сервера: `HTTP 403 — host_not_allowed`.

Это значит: данные там золотые (см. ниже), но они отдаются **только из внутренней сети города** или через авторизованную интеграцию. Любой скрипт с GitHub Actions / VPS / облака упрётся в ту же стену. **Это надо проверить с рабочей машины TENDER_FINDER до написания автоматизации** — возможно, из сети Langley / обычного интернета он открывается (блокировка может быть именно на дата-центры).

---

## Сводка: что работает, что нет

| Источник | Доступ | Что внутри | Для TENDER_FINDER |
|---|---|---|---|
| **Vancouver Open Data API** | 🟢 Публичный | Issued building permits (с 2017, обновление ежедневно) | Трейлинг-сигнал |
| **CivicInfo BC RSS** | 🟢 Публичный | Муниципальные тендеры BC, RSS-лента | Прямой |
| **Surrey GIS — FutureWorks** | 🔴 За firewall'ом | Запланированные инженерные работы по слоям | 🔥 Золото |
| **Surrey GIS — CapitalConstruction** | 🔴 За firewall'ом | Капитальные проекты города | 🔥 Высокий |
| **Surrey GIS — Applications** | 🔴 За firewall'ом | Development applications (rezoning, subdivision) | Высокий |
| **Surrey Open Data Hub** | 🟡 Проверить | Тот же датасет через ArcGIS Online (публичный CDN) | Высокий |
| **Vancouver rezoning/dev apps** | 🟡 Только веб | shapeyourcity.ca — нет API, только страницы | Средний |
| **BidCentral pre-bid** | 🟡 Email/подписка | Pre-bid проекты BC, обновление ежедневно | 🔥 Высокий |

---

## 🟢 ДОСТУПНО СЕЙЧАС

### Vancouver Open Data — Issued Building Permits
Настоящий публичный REST API (платформа Opendatasoft v2.1), работает с любой машины.

- **Каталог:** `https://opendata.vancouver.ca/explore/dataset/issued-building-permits/`
- **API-консоль:** `https://opendata.vancouver.ca/api/explore/v2.1/console`
- **Шаблон запроса:**
  `https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/issued-building-permits/records?limit=20&order_by=issuedate DESC`
- **Полезные поля для фильтра:** `TypeofWork`, `PropertyUse`, `SpecificUseCategory`, `PermitCategory`, `projectvalue`, `address`, `projectdescription`
- **Обновление:** текущий год — ежедневно; прошлые годы — статично
- **Лицензия:** Open Government Licence – Vancouver (можно использовать и републиковать)

⚠️ **Важное ограничение:** rezoning и development-permit **заявки** в этот API НЕ входят — только выданные building permits. Заявки (ранний сигнал) живут отдельно на `shapeyourcity.ca/rezoning` и `shapeyourcity.ca/development` — там только веб-страницы, без структурированного API.

### CivicInfo BC — RSS тендеров
Исходный план называл это «самым автоматизируемым источником». Открытый RSS, работает без подписки.

- **Страница:** `https://www.civicinfo.bc.ca/bids`
- Отдаёт RSS-ленту муниципальных / региональных тендеров BC

---

## 🔴 SURREY GIS — золото, но за firewall'ом

Сервер: `https://gisservices.surrey.ca/arcgis/rest/services`
Полный каталог сервисов получен. Три ключевых для TENDER_FINDER:

### Три главных сервиса
| Сервис | Endpoint | Что это |
|---|---|---|
| **FutureWorks** | `/FutureWorks/MapServer` | Запланированные инженерные работы по типам |
| **CapitalConstructionProjects** | `/CapitalConstructionProjects/MapServer` | Капитальные проекты города |
| **Applications** | `/Applications/MapServer` | Development applications |

### FutureWorks — разбивка по слоям (это и есть жила)
Каждый слой — отдельный набор запланированных работ. `MaxRecordCount: 1000`, форматы `JSON, geoJSON`.

| ID | Слой | Для TENDER_FINDER |
|---|---|---|
| 0 | FW - Drainage | 🔥 Да |
| 3 | FW - Lane | ✅ Roadwork |
| 8 | FW - Roads | 🔥 Да |
| 9 | FW - Sanitary | 🔥 Да |
| 10 | FW - Sidewalk | ✅ Site concrete |
| 11 | FW - Storm | 🔥 Да |
| 15 | FW - Turnaround | ✅ Roadwork |
| 16 | FW - Walkway | ✅ Site concrete |
| 17 | FW - Water | 🔥 Да |
| 1, 2, 4, 5, 6, 7, 12, 13, 14 | Driveway, Landscaping, Misc, Overlay, Parks, Street Signs, Streetlight, Trees | ⬜ Второстепенно |

**Шаблон запроса к слою** (например, Sanitary = 9):
`https://gisservices.surrey.ca/arcgis/rest/services/FutureWorks/MapServer/9/query?where=1=1&outFields=*&f=json`

### Другие сервисы Surrey, которые стоит глянуть
Из полного каталога — потенциально полезное гражданскому подрядчику:
`CapitalConstructionAnnualProjects` · `ICI_Data` (industrial/commercial/institutional) · `LightIndustrialProperties` · `Lots` · `RoadTenure` · `Bill44_Zoning_AffectedAreas` · `OpenData` (326 слоёв: дренаж, дамбы, flood plain и т.д.)

---

## 🟡 НУЖНО ПРОВЕРИТЬ С ТВОЕЙ МАШИНЫ

### Тест №1 — открывается ли Surrey GIS из обычной сети
Вставь этот URL в браузер с рабочего компа TENDER_FINDER:
`https://gisservices.surrey.ca/arcgis/rest/services/FutureWorks/MapServer/9/query?where=1=1&outFields=*&resultRecordCount=10&f=json`

- **Если вернулся JSON** → firewall блокирует только дата-центры. Скрипт надо крутить с локальной / офисной сети или через прокси в Канаде. Surrey-канал открыт.
- **Если снова 403 / таймаут** → нужен официальный доступ. Альтернатива: Surrey Open Data Hub (см. ниже).

### Тест №2 — Surrey через публичный ArcGIS Online
У Surrey есть публичный хаб, который раздаётся через CDN Esri (`services.arcgis.com`), а не через внутренний сервер:
`https://opendata-surrey.hub.arcgis.com/` → найди там «Development Applications» → кнопка **API / GeoService** даст публичный Feature Service endpoint, который работает отовсюду.

---

## Что делать дальше (по приоритету)

1. **Сделай Тест №1** — это решает судьбу всей Surrey-автоматизации за 2 минуты.
2. **Vancouver API работает уже сейчас** — на нём можно строить первый рабочий скрипт без всяких блокировок.
3. **CivicInfo RSS** — второй надёжный канал, тоже без преград.
4. Если Surrey GIS закрыт отовсюду → идём через **Surrey Open Data Hub** (Тест №2) или запрашиваем доступ у города (для подрядчиков это обычная практика).

**Итог:** автоматизацию надо строить на том, что реально открыто (Vancouver + CivicInfo + Surrey Hub), а не на внутреннем сервере Surrey, каким бы золотым он ни был. Сначала Тест №1 — потом решаем.
