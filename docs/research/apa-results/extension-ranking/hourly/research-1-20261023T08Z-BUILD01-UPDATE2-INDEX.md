# APA №1 — BUILD-01 | 2026-10-23 08Z | Дополнение UPDATE2 | VERIFIED SOURCE INDEX

## Воздействие на BUILD-01 (P0)

**Найдено новое после основного hourly 08Z:** 23 октября 2026 между 08:06–08:30 UTC в upstream Tapir объединены [PR #1274 GetFavoriteSettings](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1274), [#1270 ConvertRevealOffsets](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1270), [#1271 GetOpeningTransformations](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1271) и [#1102 GetStructureDisplay](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1102). Это готовые upstream реализации для проверки параметров Favorites, точности оконных откосов, трансформации Opening-tool и влияния Partial Structure Display на геометрическую приёмку. **Это НЕ установленные команды локального Tapir 1.5.10**.

**Какое ворото стало ближе:** G2/G4 — больше SOURCE-контрактов для проверки библиотек, проёмов и отображения. **Что осталось заблокировано:** G0 = BLOCKED (нет PID/loaded APX path/SHA, port/PLN, installed registration/schema); G1 = NOT_RUN (нет OFFLINE_PASS); G2 = SOURCE_ONLY (в том числе отдельные CreateSlabs/ModifySlabs scopes и BeamSegment inventory gap по №2 08Z); G3 = NOT_AUTHORIZED; G4/G5 = NOT_RUN. **Новых PASS=0, новое нативное здание не создавалось.**

[Инженерная задача #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) · [существующий компилятор PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) · [основной 08Z индекс (не изменён)](research-1-20261023T08Z-BUILD01-INDEX.md) · [отчёт №2 08Z](research-2-integration-2026-10-23T08Z-report.md).

## Публикация: все четыре приложения реально существуют и повторно проверены

| Приложение | Содержание | Git blob SHA-1 | create_file commit SHA | Readback |
|---|---|---|---|---|
| [S01–S15](research-1-20261023T08Z-BUILD01-UPDATE2-SOURCE-A.md) | SOURCE-A.md | `8f6cc756d9a33e6f755c1aec5f8a78f749a954dc` | `84d5bb78bb49b65631a63e9401c3b5f5e453d148` | EXACT |
| [S16–S30](research-1-20261023T08Z-BUILD01-UPDATE2-SOURCE-B.md) | SOURCE-B.md | `fe02d38b1d90fd4c9ebc71e3c4073db086e57c83` | `1de83a0791ed48720baa207c9dec52d913a205a6` | EXACT |
| [C01–C07](research-1-20261023T08Z-BUILD01-UPDATE2-CARDS.md) | CARDS.md | `d7f2654f463cd450ceb89ea33c38f25dce5afc4d` | `421c93d2f016395fae29c9bf64bcb71bd9ca1bfd` | EXACT |
| [A01–A02](research-1-20261023T08Z-BUILD01-UPDATE2-AUDITS.md) | AUDITS.md | `54810a13843f9f83f8b9ecadec4a731f0af748df` | `34833f5da58ccc9f2169ce86ef0160b2820ba6e8` | EXACT |

**Итого:** 30 самостоятельных SOURCE-проверок (13 PR, 9 issues, 4 официальные Graphisoft AC29 страницы, 4 прямых исходных файла), 7 полных карточек, 2 собственных контрааудита. Это 30 отдельных проверенных первоисточников/файлов, не 30 native тестов. SHA-1 — Git blob SHA; это не SHA-256 архива. После create_file каждый файл прочитан целиком и сравнен с отправленным UTF-8 текстом; перед индексом повторно проверены blob SHA всех четырёх.

## Два принципиальных отрицательных результата

1. [Issue #1042](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1042) об отсутствии composite wall corner **отозван автором** после перепроверки: не добавлять фиктивный баг и не чинить его.
2. [PR #1260](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1260) MERGED, но читает только sets своего add-on и зависит от ещё не объединённого CREATE. [PR #1233](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1233) MERGED, но пишет GDL scripts: запрещённая для исследователя мутация. Не повышать до G2 PASS.

## Адресное задание исследователю №2

1. **G0:** без установки получить Windows PID, путь фактически загруженного APX, SHA256 именно этого файла, порт, current PLN, GetAddOnVersion и registered commands. Пока этого нет, новые upstream команды НЕ использовать.
2. **G1/G2:** сохранить существующие PR74/SceneWriter, выполнить разрешённый read-only preflight/чистый compiler; отдельно квалифицировать CreateSlabs и ModifySlabs write scopes; проверить BeamSegment в финальном GUID diff и writer-required fields.
3. **G2:** зафиксировать installed Favorites, library part, marker, GDL params, ownerWall GUID и active floorplan database. Не делать trial CREATE.
4. **G4:** запретить blind full GetDetailsOfElements sweep до проверки безопасности; фиксировать Partial Structure Display, dirty-state и guarded Save/Open. При unknown — STOP.
5. **Вне P0:** IFC/Hotlink/DXF/PDF/MEP/SAF/Publisher не расширять без доказанного практического blocker.

## Источники состояния и границы

Прочитаны [NEXT_RESEARCH_PRIORITIES](../NEXT_RESEARCH_PRIORITIES.md), [матрица 61](../priority_matrix_20261018.json), №2 08Z и [PROJECT_PLAN rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/049576378c961c5d7a9a62611f4091e3da70d309/docs/research/apa-results/control/PROJECT_PLAN.json) — только чтение. Отчёт №3 за 23 октября по проверенным именам не найден, что не доказывает его отсутствия. Opera Browser Connector недоступен (один link требует интерактивного ввода, второй browser not connected); пользовательские вкладки не изменялись.

**Статусы:** SOURCE=30; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0 **в рамках этого дополнения**. GitHub исследовательская публикация DONE_PUBLISHED только после exact readback индекса. Main, код, PLN/APX, установка, LIVE, PR merge, Work/Codex/Arena, платные API не изменялись. Важность 0–100 экспертная; 100× не заявляется. **MODEL_MODE_NOT_VERIFIABLE.**
