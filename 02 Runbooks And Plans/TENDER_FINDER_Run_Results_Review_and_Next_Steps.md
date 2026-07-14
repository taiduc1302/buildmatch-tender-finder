# TENDER_FINDER — разбор результатов прогона + код-фиксы + следующие шаги

_Дата: 22 июня 2026. По итогам живого sweep'а (run_log.json + 15 JSON-выгрузок)._

## Итог одной строкой
Механически sweep отработал (резолвил endpoint'ы, вытащил строки), **но качество данных очень разное**. Три ядровых источника — золото и уже загружены; половина остального — не тот слой / трейлинг / мусор. Главный вывод: discover нельзя пускать без фильтра слоёв и проверки атрибутов.

---

## 1. Вердикт по каждому из 16 источников

| Источник | Строк | Что реально вернулось | Вердикт | Действие |
|---|---|---|---|---|
| **Township of Langley** | 782 | Реальные заявки (RZ/SD/DP, описание, статус, **per-record OurCity ссылки**) | ✅ **Золото** | **Загружено 15**; endpoint закреплён |
| **Maple Ridge** | 879 | Реальные заявки (type/subtype/lots/stage/адрес) | ✅ **Золото** | **Загружено 15**; endpoint закреплён |
| Surrey (ручной lead screen) | 20 | Отобранные вручную заявки | ✅ Загружено ранее | Оставить |
| **Surrey — API** | 13 770 | **«Subdivision Markers»** (геодезические марки, Morgan Creek) — НЕ заявки | ❌ **Не тот слой** | Перепинить на `…/Development Applications/FeatureServer/0`, проверить поля |
| Surrey — FutureWorks | 0 | Отключён (gated, ждёт офис-теста) | ⏸ Ждёт Тест №1 | Прогнать из сети TENDER_FINDER |
| City of Langley | 0 | web_page, API нет | ⏸ Ручной / P3 | LLM-чтение портала + месячный PDF |
| Abbotsford | 503 | Application **AREAS**: только DEV_FILE + статус, без адреса/скоупа | 🟡 Тонко | AMANDA-join или P3 перед загрузкой |
| Coquitlam | 470 | Полигоны **Neighbourhood Plan** (NP_*) — не заявки | ❌ Не тот слой | Перерезолвить на dev-app слой |
| Delta | 2 024 | Building/Plumbing **permits** (интерьер/SFD/completed) | 🟡 Трейлинг | Понизить до «permits», не лиды |
| New Westminster | 1 346 | Building/Plumbing/**Watering** permits | 🟡 Трейлинг | Понизить; искать dev-app слой отдельно |
| Burnaby | 0 | web_page, API нет | ⏸ Ручной / P3 | Council / public hearings |
| District of North Van | 7 509 | Полигоны **DPA hazard** (Creek/Slope/Wildfire) | ❌ Мусор | Denylist теперь режет |
| Port Coquitlam | 2 | **ALR-полигоны**, только геометрия | ❌ Мусор | Richness-gate теперь режет |
| Vancouver — building permits | 20 000 | Реальные выданные разрешения | 🔵 Контекст/трейлинг | Оставить (не ядровая гео) |
| Vancouver — city projects | 936 | Капитальные проекты (title + link) | 🔵 Контекст | Оставить |
| Vancouver — rezoning | 20 000 | = building permits (**slug fallback**) | ❌ Не то (дубль) | Чинить ODS-fallback; rezoning живёт на shapeyourcity (без API) |
| Vancouver — dev-permits | 2 | = business-licences (**slug fallback**) | ❌ Не то | Чинить ODS-fallback |

**Резюме:** 3 золото · 2 трейлинг · 2 контекст · 9 не-тот-слой/мусор. То есть «успешный» прогон по факту дал ~5 полезных источников из 16 — ровно поэтому нужен фильтр.

---

## 2. Что загружено в Future_Projects
**+30 строк** (15 TOL + 15 Maple Ridge), отобраны фильтром civil-релевантности из 782 и 879, проскорены по весам v2, рядом с 20 Surrey → **итого 50 лидов по 3 ядровым муниципалитетам**. Все: Verification = Needs Review, реальные source URL (TOL — даже ссылка на каждую заявку), горизонт по стадии. Owner у муниципальных таблиц = «Not available» → нужен ручной второй проход.

---

## 3. Код-фиксы

### Уже применил в `tenderfinder_agent2.py`
1. **Закрепил проверенные endpoint'ы** (TOL `services5/frpHL0Fv8koQRVWY/…/FeatureServer/1`; Maple Ridge `geoservices.mapleridge.ca/…/MapServer/1`; кандидат Surrey-public). Принцип «prove then pin» — чтобы повторный discover не уплыл на чужой слой.
2. **Denylist слоёв** (hazard/DPA/marker/watering/ALR/reserve/neighbourhood plan/asset/facility/…): отсекает слои-ловушки по имени на этапе discovery. Проверено: режет Subdivision Markers, DPA hazard, Lawn Watering, ALR, Neighbourhood Plan; пропускает реальные dev-app слои.
3. **Attribute-richness gate**: если слой отдаёт только геометрию/OBJECTID (как ALR Port Coquitlam) → ошибка «это не заявки». Проверено на реальных данных.
4. **Подтверждённые алиасы полей** (Folder_Number, ReferenceFile, Folder_Status, StatusDescription, Street, WorkProposed, SubType, Task_Type) — устойчивая нормализация под реальные схемы TOL/MR.

`py_compile` OK; гварды протестированы против настоящих плохих выгрузок.

### Рекомендую применить в `tenderfinder_raw_sweep.py` (исходник свипа у меня не было — вот точечные изменения)
1. **Убрать тихий ODS-fallback.** Если запрошенного slug нет — падать/скипать с явной ошибкой, НЕ хватать похожий датасет. Именно это дало `van_rezoning → issued-building-permits` и `van_devpermits → business-licences`.
2. **Тот же denylist при ранжировании кандидатов** `arcgis_hub_discover` / `arcgis_map_discover`: предпочитать слой, в имени которого есть «application(s)» и у которого в пробной записи есть app-поля; резать area/overlay/permit/marker.
3. **Richness-gate после выгрузки** (геометрия-онли → reject).
4. **Building-permit слои** помечать Horizon = trailing, не путать с dev-applications.
5. **web_page источники** (City Langley, Burnaby) — построить P3-экстрактор (LLM-чтение страницы), а не скипать.
6. **Пинить разрешённые хорошие endpoint'ы в конфиг** после первого удачного прогона.

---

## 4. Следующие шаги (по приоритету)
1. **Example Reviewer смотрит 50 лидов** в Future_Projects (Surrey 20 + TOL 15 + MR 15) — гейт ценности, теперь по 3 ядровым муниципалитетам сразу.
2. **Перепинить Surrey-public dev-apps слой** (`Development Applications/FeatureServer/0`) и проверить, что отдаёт заявки, а не марки; затем при желании догрузить выверенный Surrey-API набор к 20 ручным.
3. **Перерезолвить Coquitlam** на реальный dev-app слой; **P3-экстрактор** для City of Langley + Burnaby (web_page).
4. **Тест №1** (Surrey FutureWorks из офисной сети TENDER_FINDER) — по-прежнему разблокирует капитально-servicing трек.
5. **Применить фиксы свипа** (denylist + richness + no-silent-fallback) → следующий прогон будет чистым.
6. ⏰ **Выгрузить MPI** до ~30 июня (осталось ~8 дней).
7. **Ручной второй проход** (ODI/COSMOS-эквивалент / открыть полные отчёты) по топ-лидам перед BD-outreach — owner почти везде «Not available».

---

## 5. Финальный пакет файлов
- **`TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx`** — операционный трекер: 50 лидов в Future_Projects (3 муниципалитета), очищенный Source_Register (68), Run_Queue с вердиктом по каждому источнику, Cleanup_Log. **Главный рабочий файл.**
- **`tenderfinder_agent2.py`** — закалённый коллектор (пины + denylist + richness-gate + алиасы; источники vancouver/surrey/langley_tol/maple_ridge).
- **`TENDER_FINDER_Municipal_Run_Packs.md`** — процедура прогона + endpoint'ы по муниципалитетам.
- **`TENDER_FINDER_Run_Results_Review_and_Next_Steps.md`** — этот разбор.
- **`TENDER_FINDER_Project_Plan_Role_Goal_Tasks_Instructions.md`** + **`TENDER_FINDER_Project_Plan_Supplement_v2.md`** — план (роль/цель/задачи) и дополнение.
