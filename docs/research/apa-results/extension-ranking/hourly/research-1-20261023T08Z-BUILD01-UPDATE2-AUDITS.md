# APA №1 — BUILD-01 | 2026-10-23 08Z UPDATE2 | два собственных контрааудита

## A01 — первоисточник, версия, статус, совместимость

**Вопрос:** можно ли переносить MERGED upstream 2026-10-23 в установленный Tapir 1.5.10 на Archicad29 build5101?

**Проверка:** PR #1274, #1270, #1271, #1102, #1260, #1233 прочитаны непосредственно через GitHub fetch_pr; merged=true, merge SHA известны, но версии регистрации различаются: 1.7.3 у первых трёх, #1260 и #1233; #1102 зарегистрирован как 1.7.2. Источник upstream AddOnVersion.hpp main имеет ADDON_VERSION 1.7.3 (blob 83856d53b18c4a63887474a50cb7db504b6d0741), а сохранённый каталог APA tapir-scene-live.json относится к 1.5.10 (blob e8ad53b6ea7c19dc34cbdcb723a79be995639cd7). Не проверены loaded APX, SHA, PID, port, actual registration/schema.

**Независимая Graphisoft AC29 сверка:** официальная [Favorites](https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-56.htm) подтверждает проектные параметры Favorite, но не существование нового JSON метода GetFavoriteSettings в 1.5.10. Официальный [Partial Structure Display](https://help.graphisoft.com/AC/29/INT/_AC29_Help/050_ViewsVB/050_ViewsVB-94.htm) подтверждает поведение видов, но не регистрацию GetStructureDisplay в APX.

**Контрпример:** #586 и #683 объединены, но их авторы прямо описывали отсутствие DevKit/Archicad live тестов при подготовке. MERGED — не бинарная приёмка. #1011 OPEN и stacked on #918; нельзя считать его готовым AC29 ModifyOpenings.

**Итог A01:** SOURCE_CONFIRMED для upstream контрактов, LOCAL_INSTALLED_NOT_VERIFIED. G0 BLOCKED. №2 должен подтвердить PID→loaded APX→SHA256→GetAddOnVersion→IsAddOnCommandAvailable, без установки/изменения APX.

## A02 — применимость к BUILD-01 и недублирование

**Вопрос:** приближают ли найденные механизмы к нативному целому зданию, не подменяя PR74/SceneWriter?

**Проверка по исходникам:** [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) требует G0→G1→G2→G3→G4→G5 и строго отдельные доказательства. [SceneWriter PR162](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py#L976-L1025) содержит вторую mutation ModifySlabs после CreateSlabs. [№2 08Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T08Z-report.md) описывает потенциальную потерю BeamSegment в final GUID diff. Ни одна новая upstream команда не снимает эти два местных барьера.

**Контрпримеры против ложной готовности:**
- [issue #1042](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1042) закрыт потому, что АВТОР ОТОЗВАЛ исходный репорт о пропавших composite corners после перепроверки 119 стен. Не добавлять фиктивный gap.
- [PR #1260](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1260) MERGED, но только читает element sets своего add-on; создание наборов (#1188) не merged. Это не замена BIM Graph.
- [PR #1233](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1233) MERGED, но пишет GDL scripts; исследователю WRITE запрещён, к P0 не подключать.
- [PR #1351](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1351) OPEN и даёт 2D triangles, не 3D BREP.
- [issue #1093](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1093) показывает collision=true даже для корректного L-стыка; collision нельзя использовать как бинарный fail.
- [issue #1381](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1381) демонстрирует loss unsaved changes на AC28, но не на AC29 build5101; это ограничение для safe policy, не локальный доказанный дефект.

**Положительный отбор:** C01 Favorite read-only — подготовка G2; C02 reveal offset — точность G2/G4 при composite; C04 Partial Structure Display — корректность визуального G4; C05 безопасный readback — предотвращение crash; C06 active floorplan context — CreateWindows/Doors; C07 GuardedSave — G4. C03 Opening-tool conditional, не первый обязательный набор.

**Итог A02:** новых OFFLINE/LIVE/ACCEPTED нет. Не создавать второй writer, adapter, Clone, MEP/IFC/Publisher backlog. Адресное задание №2: (1) G0 loaded APX, (2) G1 существующий compiler/read-only preflight, (3) G2 Slab double scope + BeamSegment final diff, (4) G4 guarded save/dirty-state + safe geometry inventory. Никакого native WRITE до отдельного разрешения.

## Проверка организационного состояния

Прочитаны NEXT_RESEARCH_PRIORITIES.md (blob 6f074693360231c5cb42ada815984a6b0dd504c0), матрица 61 (blob 9cb5e6f2a59f80762cc77073eeb10404829af75a), №2 08Z (blob 4156c7bdf90b5ce5e0ecaf92946be53e25bb9fae), issue192 и исторический PROJECT_PLAN.json revision182 по commit 049576378c961c5d7a9a62611f4091e3da70d309. Исторический файл только чтение. Последний отчёт №3 за 23 октября по проверенным именам не найден; это не доказательство отсутствия других имён.

Opera Connector: один link потребовал интерактивный ввод, второй вернул Browser not connected. Новые вкладки не создавались, пользовательские не закрывались. Использованы прямые GitHub и официальные Graphisoft AC29 первоисточники.

**MODEL_MODE_NOT_VERIFIABLE.**
