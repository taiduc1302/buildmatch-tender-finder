# TENDER_FINDER Tender Intelligence — дополнение к плану (v2-delta)

_Дополняет «TENDER_FINDER_Project_Plan_Role_Goal_Tasks_Instructions» по новому пакету файлов. Дата: 22 июня 2026. Роль, цель и scope-якорь — без изменений, см. v1._

---

## 1. Что нового в этом пакете (и что из этого новое по сути)

| Файл | Новое? | Что это значит для плана |
|---|---|---|
| **TENDER_FINDER_Tender_Intelligence_Working_Master_v3.xlsx** | 🟢 Да, крупное | **Шасси построено.** 19 вкладок. Внутрь зашит мой каркас A–G, фазы, гейты, юр-граница, scope-якорь. **Задачи A и E фактически выполнены** (см. §2). |
| **TENDER_FINDER_Surrey_Prompt_Review_RU.docx** | 🟢 Да, ценное | Саморазбор промпта, которым сделан Surrey-список, + **улучшенный промпт v2 с формализованными весами**. Прямо закрывает пробел «scoring не формализован» из Задачи G. |
| **TENDER_FINDER_Tender_Intelligence_Process__1_.docx** | 🟡 Переработка | Чистая реструктуризация Data Collection Plan (PART A–I, расширенный source register). Та же суть, лучше структура. Противоречий с планом нет. |
| **deep-research-report__1_.md** | ⚪ Не новое | Это Surrey lead screen в исходном markdown (с цитатами/диаграммами). Подтверждает: список сделан веб-ресёрчем. |
| Surrey Lead Screen (.docx/.pdf), Data Collection Plan, прочее | ⚪ Повтор | Уже разобрано в v1. |

**Вывод:** фронт сдвинулся. Два из моих «могу сделать дальше» (собрать Excel-шасси; прогнать карту рынка) — уже сделаны кем-то и сведены в воркбук. Значит, мой следующий ход меняется (§4).

---

## 2. Обновление статусов задач

- **Задача A (шасси) — ✅ ВЫПОЛНЕНА, сверх спецификации.** Я закладывал 5 вкладок — построено 19: Config_Scope, Active_Tenders, Future_Projects (с авто-формулой Fit Class и дропдаунами), Source_Register, Municipal_Coverage, Rejected_Archive, Weekly_Review_Log, Dashboard, Automation_Plan, Paid_Intelligence, Prompt_Pack, Phased_Rollout, Project_Plan и др. Статус в самом воркбуке: «A — Ready».
- **Задача E (карта рынка) — ✅ СВЕДЕНА В ВОРКБУК.** Source_Register = **68 источников**, классифицированы по категориям A–G, протиражированы Tier 1–3, с access-статусом, форматом, automation-feasibility, стоимостью. Плюс Municipal_Coverage (25 муниципалитетов), Automation_Plan (ранжирование), Paid_Intelligence (сравнение). Это и есть deliverable из брифа Full Market Source Map.
- **Новый зазор, который я закрыл в этом ходе — ✅ Surrey-данные загружены.** Воркбук был «красивым пустым шасси»: Active_Tenders и Future_Projects — 0 строк данных. Его собственный Dashboard помечал «загрузить Surrey top-20» как действие, которое «turns the workbook from framework into proof-of-value». Я загрузил **20 проверенных Surrey-лидов** в Future_Projects (см. §5).
- **Задачи B, C, D, F, G — без изменений по статусу** (см. §3 и §4). Гейты по-прежнему открыты.

---

## 3. Находки по качеству воркбука (то, что надо знать перед тем, как доверять цифрам)

Воркбук собирался слиянием нескольких прогонов (английского + русского), и слияние оставило артефакты. Я их **не стал авто-удалять** — часть может быть намеренной (двуязычие), а часть требует человеческого решения. Все они теперь зафиксированы во вкладке **Cleanup_Log** воркбука. Конкретно:

1. **Дублирование строк по языкам.** Вкладки **Automation_Plan, Priority_Monitoring, Phased_Rollout** содержат один и тот же контент дважды — английский блок + русско-смешанный блок. Решение человека: оставить двуязычно или удалить лишний языковой блок.
2. **Склеенные значения в ячейках.** В **Source_Register** и **Municipal_Coverage** часть ячеек содержит слитые значения через «;» (напр. `Working; Verified; Not tested`, `weekly; Regular; Frequent`). Это мешает фильтрации и будущей автоматизации. Авто-схлопывать рискованно (можно потерять инфо) — нужен ручной выбор одного значения на ячейку.
3. **Плейсхолдер-URL.** Несколько строк Source_Register помечены `Needs exact URL` (Pitt Meadows, Procore, LeadManager, client/FN/port PR). Дорешить в рамках продолжения Задачи E.
4. **Мелочь по Dashboard.** Счётчики Fit Class (`COUNTIF … "Strong Fit"`) считают значения колонки M, которая является формулой — пересчитается при открытии в Excel. После загрузки Surrey там должно появиться 6 Strong Fit / 14 Good Lead в Future_Projects.

Ни одна из этих находок не критична, но без их вычистки Source_Register пока «читаемый людьми», а не «готовый к автоматизации».

---

## 4. Обновлённая немедленная последовательность (фронт сдвинут)

Поскольку A и E готовы, «что делать прямо сейчас» переписывается так:

**Сделано в этом ходе (мной):**
1. ✅ Загрузил Surrey top-20 в Future_Projects (proof-of-value внутри трекера).
2. ✅ Обновил Prompt 1 в Prompt_Pack до формализованной v2 (из Prompt Review).
3. ✅ Зафиксировал находки по качеству в Cleanup_Log (без разрушающих правок).

**Немедленно (человеческие действия — я их сделать не могу):**
4. ⏰ Выгрузить BC Major Projects Inventory, пока страница жива (≈до 30 июня — осталось ~8 дней).
5. **Тест №1** по Surrey с рабочего компа TENDER_FINDER — 2 минуты, открывает развилку автоматизации (Задача B). Результат записать в Source_Register (access type).
6. **Показать Example Reviewer** загруженный Future_Projects (6 Strong Fit сверху) и получить вердикт continue/adjust/stop. Теперь это удобно — он смотрит лиды прямо в трекере, а не в отдельном PDF.
7. Завести `estimating@example.com` и начать подписки BC Bid / bids&tenders / CivicInfo (Задача D) — параллельно.

**Дальше (по гейтам):**
8. Если Example Reviewer «да» → прогнать **Township of Langley** и **Maple Ridge** уже промптом v2 (Задача C), писать в те же вкладки.
9. Вычистить артефакты слияния в Source_Register/Municipal_Coverage (§3) → тогда реестр станет automation-ready.
10. Прогнать `tenderfinder_agent2.py --demo`, затем `--source vancouver` (Задача F, без блокеров).
11. По итогам Теста №1/№2 — включить Surrey в скрипт нужным каналом.

---

## 5. Что именно загружено в Future_Projects (и как считались баллы)

20 лидов из Surrey lead screen, каждый — со стабильным Project ID (`SURREY-<appno>`), реальным Surrey-URL (Planning Report PDF / in-process список / Council-минуты), статусом **Needs Review** (ни один не «Verified» — ручной второй проход по ODI/COSMOS ещё не делался) и горизонтом, помеченным «estimated only».

**Баллы (0–100)** проставлены по весам из улучшенного промпта: civil-scope 35 / type-fit 25 / stage 20 / location 10 / owner-visibility 10. Итог:

- **Strong Fit (≥85) — 6 лидов, показать Example Reviewer первыми:** 2750 194A St (Wesgroup, industrial, 88) · 3141 190 St (warehouse + ROW/road-closure, 86) · 19135/19143 30 Ave (Beedie warehouse, 86) · 19066 20 Ave (Beedie business park, 86) · 18875 52 Ave (Patton&Cooke + environmental lot, 85) · 13924 56 Ave (68-lot subdivision, mass grading, 85).
- **Good Lead (70–84) — 14 лидов:** townhouse/subdivision файлы Cloverdale/Clayton/Fleetwood/South Surrey + остальные industrial.

**Важный практический вывод из Prompt Review, встроенный в Задачу C:** у 13 из 20 лидов owner = «Not available». Перед outreach по топ-лидам нужен обязательный шаг — открыть полный Planning Report PDF и вытащить owner/applicant/agent/civil-consultant + сверить стадию в ODI/COSMOS. Это и есть «manual second-pass», который отделяет lead-identification (можно автоматизировать) от tender-timing (нельзя без ручной проверки).

---

### Итог дополнения
Проект продвинулся: шасси построено, карта рынка сведена, промпт улучшен. Я загрузил доказанные Surrey-данные внутрь трекера (теперь это не пустой каркас, а живой proof-of-value с 6 приоритетными лидами), обновил скоринг-промпт до формализованной версии и пометил артефакты слияния для ручной вычистки. Два гейта (Тест №1 + вердикт Example Reviewer) и MPI-дедлайн 30 июня — по-прежнему то, что блокирует следующий шаг, и это человеческие действия. Дальше логично: вердикт Example Reviewer → Langley/Maple Ridge промптом v2 → вычистка реестра → автоматизация доказанного.
