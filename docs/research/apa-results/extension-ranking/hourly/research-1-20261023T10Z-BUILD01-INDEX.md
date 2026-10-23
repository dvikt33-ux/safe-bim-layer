# APA №1 | 23.10.2026 10Z | BUILD-01 | исследовательский индекс

## Воздействие на BUILD-01 — первое и главное

**Найдено:** [Tapir PR1134](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1134) MERGED 23.10 10:46:57Z: готовые upstream `RegularizePolygons/RegularizePolylines` для проблемных контуров Slab, с 0..N валидными полигонами и ancestry. [Tapir PR1434](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1434) MERGED 22.10: готовые `ProjectHealthCheck.py` и `SolidOperationExplorer.py` для дополнительных проверок. [PR1395](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1395) OPEN описывает конкретную ошибку размеров объектов AC29 build5101 при смене libraryPart.

**Какие ворота ближе к PASS:** G2 — источник регуляризации проблемных контуров и проверка размеров libraryPart; G4 — дополнительные диагностики ID/дублей/SEO. **Только SOURCE_ONLY. Ни одни ворота не стали PASS.** Регуляризация не обязательна, пока не показан невалидный контур BUILD-01. AABB/2D triangulation не заменяют BREP.

**Что остаётся BLOCKED:** G0 — неизвестны фактически загруженный APX SHA, PID, port/PLN и runtime schema; G1 — нового двухэтажного OFFLINE_PASS нет; G2 — [№2 10Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T10Z-report.md) выявил `DUAL_WRITE_APPROVAL_NOT_ENFORCED` для CreateSlabs→ModifySlabs, значит WRITE_BLOCKED; G3 не санкционирован; G4 BREP/Save/Open не испытаны; G5 не начато. **Здание не создавалось.**

**Главная инженерная задача:** [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). Единственный исполнитель — существующие [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) / DynamicCommands → BIM Graph → SceneWriter → SQLite. Никаких новых writer/router/CloneNativeGroupV1.

## Проверенные приложения и прямые ссылки

| Файл | Содержание | Git blob SHA-1 (проверен повторным fetch_file) |
|---|---|---|
| [SOURCE-A](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T10Z-BUILD01-SOURCE-A.md) | S01–S14; 14 прямых проверок | `b45f42a1b9548d420287f70af7a81200fdf21556` |
| [SOURCE-B](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T10Z-BUILD01-SOURCE-B.md) | S15–S28; 14 прямых проверок | `95f568a75b92913db3dcf3a2b9740c05b22172fa` |
| [CARDS](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T10Z-BUILD01-CARDS.md) | 6 карточек решений с версиями, контрактами, рисками и заданиями №2 | `213b91fe3cd6898e557622f3d45896d02460aa9e` |
| [AUDITS](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T10Z-BUILD01-AUDITS.md) | 2 контрааудита: совместимость и недублирование | `eb5d25ef26dc94b3db47cbd2347a1e00dbe4ccdf` |
| [MANIFEST](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T10Z-BUILD01-MANIFEST.json) | readback 4 приложений, Git blob SHA-1, commits | `d9a534e42b0cd5ee2d2ae8dc41397425fdb32d3b` |

**Счёт:** 28 реально прочитанных независимых GitHub PR/issues (S01–S28), плюс прямое чтение PR1134/PR1434 patches, MIT LICENSE и проектных документов; шесть карточек, два собственных контрааудита. **Не 30.** Важность 0–100 — только экспертная; benchmark не выполнялся. `SOURCE=28, OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0` для данного прохода.

## Адресное задание исследователю №2 и инженерному исполнителю

1. **G0 (P0):** read-only PID→loaded APX path→SHA256, порт, активный scratch PLN, GetAddOnVersion, exact runtime schema. Без этого не объявлять RUNTIME_READY.
2. **G1 (P0):** реальный read-only authored preflight двух этажей через существующий PR74, typed DAG/plan hash, без native CREATE.
3. **G2 (P0):** отдельно санкционируемые CreateSlabs и ModifySlabs; readback floorIndex/material/thickness/holes; обязательные native Walls/Slabs/Roof/Doors/Windows, hostWall GUID. До реализации dual-approval — WRITE_BLOCKED.
4. **G2 (условно):** если preflight показывает невалидный polygon, оценить PR1134 (в upstream 1.7.2, не локальной 1.5.10), проверить split 0..N/ancestry/area; без автоматической замены проектной геометрии.
5. **G4 (условно):** добавить сравнение ProjectHealthCheck/SEO из PR1434 как вспомогательное SOURCE; не считать его независимым BREP. Не запускать write-actions палитры.
6. **G3–G5:** только после отдельного инженерного допуска на новую scratch PLN/port/plan hash, затем GuardedSave, GUI close/reopen, independent BREP/GUID/host/material; второе независимое здание позже.

## Контекст и контрааудит

Прочитаны [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md), [матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) (`count=61`, полный пересчёт формул не выполнялся), [№2 10Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T10Z-report.md), [последний найденный аудит №3 20.10 07Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07.md), [исторический PROJECT_PLAN.json rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/049576378c961c5d7a9a62611f4091e3da70d309/docs/research/apa-results/control/PROJECT_PLAN.json) (revision=182, 91 tasks), только чтение. Последние материалы №3 после 20.10 07Z по проверенной hourly директории не обнаружены.

**Контрааудит A01:** upstream merge не подтверждает локальную 1.5.10; не проверенный DevKit и отсутствие LIVE делают новое решение SOURCE_ONLY. **Контрааудит A02:** PR1134/1434 не устраняют G0 или двойное разрешение Slab, а G4 без BREP не проходит. Полные доказательства — [AUDITS](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T10Z-BUILD01-AUDITS.md).

**Opera:** connector проверен; одно подключение `Browser not connected`, другое запросило интерактивное подтверждение; пользовательские вкладки не изменены. GitHub connector использован напрямую.

**Публикация:** приложения созданы через `create_file` с явным `branch=research/apa-extension-ranking-hub-20261018`, затем `fetch_file` точное сравнение текста и Git blob SHA; манифест проверен. Этот индекс публикуется последним. `SHA256` файлов не вычислялся (только Git blob SHA-1). Не изменены main, исходный код APA, PLN/APX, установка, LIVE, PR merge, PROJECT_PLAN.

`MODEL_MODE_NOT_VERIFIABLE`.
