# APA №1 — BUILD-01 | 23 октября 2026, 09Z | SOURCE VERIFIED INDEX

## 1. Воздействие на BUILD-01 (P0)

**Новые полезные доказательства этого прохода:** [Tapir issue #481](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/481) — на AC29 build5003 CHE Mac CreateWindows/CreateDoors возвращали GUID при отсутствии фактического проёма; [#573](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/573) — SetStories мог вернуть success с неправильными абсолютными отметками; [#439](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/439) — пакет сложных Slab приводил к аварии на AC28; [#604](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/604) — accepted payload мог не применить Slab holes и Roof thickness. Эти репорты НЕ доказывают те же ошибки на локальной AC29 build5101 / Tapir1.5.10. Готовые пути снижения риска: existing GetStories/readback, поэлементный Window/Door host GUID readback, строгая проверка holes, использование уже существующего SceneWriter с двумя отдельными разрешениями на Slab CREATE/MODIFY, guarded Save/Open.

**Какое ворото приблизилось к PASS:** G1/G2/G4 получили проверяемые критерии, но ни одно не получило PASS. G0 всё ещё **BLOCKED**: отсутствуют read-only доказательства PID → loaded APX path/SHA256, port/PLN, GetAddOnVersion, installed registration/schema. G1 фактический OFFLINE_PASS не выполнялся. G2 SOURCE_ONLY. G3 NOT_AUTHORIZED. G4/G5 NOT_RUN. **Новых нативных зданий = 0; ACCEPTED = 0.**

Прямые ссылки: [главная задача BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) · [компилятор PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) · [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py) · [отчёт №2 09Z](research-2-integration-2026-10-23T09Z-report.md).

## 2. Опубликованные приложения, существование и SHA проверены

| Приложение | Содержание | Git blob SHA-1 | create_file commit SHA | fetch_file |
|---|---|---|---|---|
| [SOURCE-A](research-1-20261023T09Z-BUILD01-SOURCE-A.md) | S01–S15, 15 SOURCE-проверок | `ad730aca70b4a8daf074f22ced6faf7143d10366` | `08eb6c0e95c0af27abfaf0c87f1f83001263c990` | SHA_EXACT |
| [SOURCE-B](research-1-20261023T09Z-BUILD01-SOURCE-B.md) | S16–S30, 15 SOURCE-проверок | `f663b708023d0a2ac7c653ff86d251f99e279b79` | `93718fcfc4231062b1956e709f7408742606e645` | SHA_EXACT |
| [CARDS](research-1-20261023T09Z-BUILD01-CARDS.md) | 7 полных карточек C01–C07 | `5d26b79531b1350d9e7cae261f6e9766cd96de2c` | `5d5ad48cb0c13d71c53d8827ec25a640ce2dc274` | SHA_EXACT |
| [AUDITS](research-1-20261023T09Z-BUILD01-AUDITS.md) | 2 контрааудита A01/A02 | `a121a27a017d6554875a004c59ca687eaa0dff83` | `8bdeb3319d5b1dd0bc99b3bf125303e8734ecdf9` | SHA_EXACT |
| [MANIFEST](research-1-20261023T09Z-BUILD01-MANIFEST.json) | JSON file→SHA + readback | `52516ded0a8435718fb2898a67b10b8b4f59aaa6` | `962ec15edf6784dfa3daae4bdc60722833a4d3f5` | EXACT |

**Итого:** 30 отдельных предметных SOURCE-проверок: 27 GitHub issue/PR, 2 официальных Graphisoft AC29 первоисточника, 1 лицензия Tapir 1.5.9 MIT. Источники по нескольким темам являются внешними репортами/предложениями, а не локально воспроизведёнными ошибками или готовыми командами. Счёт 30 не означает 30 нативных тестов. 7 карточек, 2 контрааудита. Все приложения опубликованы ДО индекса; blob SHA проверены повторным fetch_file.

## 3. Семь готовых маршрутов без второго writer

C01 — G0 PID/loaded APX/SHA и runtime schema; C02 — G1 GetStories/storyBindings без SetStories; C03 — G2 Window/Door GUID+host verification; C04 — G2 Slab material/holes и раздельные WRITE scopes; C05 — G2/G4 Roof native geometry readback; C06 — G2 AC29 Library Manager/Favorites; C07 — G4 GuardedSave + reopen + all-database inventory. **Важность 0–100 экспертная, не benchmark.** Новые upstream команды не считаются установленными.

## 4. Контрааудиты и новые факты №2

A01: версия/совместимость и ложное MERGED→INSTALLED. A02: применимость к #192 и недублирование PR74/SceneWriter. Свежий [№2 09Z](research-2-integration-2026-10-23T09Z-report.md) подтвердил по исходникам: Slab SceneWriter поддерживает два этажа через CreateSlabs→ModifySlabs, но требует две санкции; PR149 verifier ограничен floorIndex=0. Beam NativeAdapter существует, но run_project подключает только roof adapter, поэтому optional Beam без opt-in может получить UNSUPPORTED_WRITE_RECIPE. BeamSegment inventory gap остаётся условным. Эти выводы SOURCE, не OFFLINE/LIVE.

## 5. Прочитанные контрольные документы

- [NEXT_RESEARCH_PRIORITIES.md](../NEXT_RESEARCH_PRIORITIES.md), Git blob `6f074693360231c5cb42ada815984a6b0dd504c0`.
- [Матрица 61](../priority_matrix_20261018.json), blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`; [кандидаты 61](../candidates.json), blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`. Оба массива по 61, не новые исследования.
- [№2 09Z](research-2-integration-2026-10-23T09Z-report.md), [№2 08Z](research-2-integration-2026-10-23T08Z-report.md). Последний прямо найденный аудит №3 — [20.10 07Z](audit-2026-10-20-07.md); 23.10 04–09Z по проверенным именам не найден, полнота архива №3 не заявляется.
- [PROJECT_PLAN.json rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/049576378c961c5d7a9a62611f4091e3da70d309/docs/research/apa-results/control/PROJECT_PLAN.json): revision=182, 91 задача, исторический read-only; исходник не изменялся.
- Предыдущий [№1 08Z UPDATE2](research-1-20261023T08Z-BUILD01-UPDATE2-INDEX.md) проверен; новая работа не повторяет его четыре merged PR #1274/#1270/#1271/#1102 как новые находки.

## 6. Адресная передача №2

**Первым:** PID→loaded APX path→SHA256, port/current PLN, GetAddOnVersion, installed command registration/schema; отдельная квитанция G0. **Вторым:** реальный read-only preflight PR74 нового двухэтажного typed DAG; без fake offline. **Третьим:** проверка exact host-wall GUID для окон/дверей, Slab holes+material double scope, supported SinglePlane Basic Roof, Beam opt-in и child GUID final inventory. **Четвёртым:** только отдельный исполнитель после разрешения владельца может проводить G3/G4/G5 на новой scratch PLN; no retry CREATE при UNKNOWN.

## 7. Границы действий

Исследование SOURCE_ONLY. Main, код APA, исходные PLN/APX, установки, LIVE, PR merge, Work/Codex/Arena, платные API не затрагивались. Opera Browser Connector возвращает `Browser not connected`; пользовательские вкладки не закрывались. Режим модели проверить невозможно: **MODEL_MODE_NOT_VERIFIABLE**.
