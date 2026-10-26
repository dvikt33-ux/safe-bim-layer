# Реестр включения октябрьских исследований Archicad в шаблон AC29

**Период:** 01–26 октября 2026 года. **Дата инвентаризации:** 26.10.2026.  
**Назначение:** добавить полученные исследования Archicad/APA в единую базу знаний шаблона без подмены исследований результатами LIVE-приёмки.  
**Продукт:** `AC29_RU_SBIM_1.0`, основная среда Archicad 29.2.1 build 5101 RUS FULL.  
**Исходная ветка сборщика:** `feature/working-archicad-mvp`, зафиксированный HEAD перед консолидацией `792f7d879bd62f0489eb0757179ed5efa198f016`.  
**Действия этого включения:** документация и реестр обнаруженных GitHub-веток. Ни Archicad, ни PLN, ни APX, ни исходный сборщик, ни `main` не менялись.

## 1. Что здесь означает «принять исследования»

1. **Включить в архив и учитывать** все найденные источники, версии, положительные и отрицательные результаты, не стирая оригиналов.
2. **Отдельно решать применимость к шаблону.** Исследование инструмента НЕ означает его установку и автоматическое включение в `.tpl`.
3. **Не повышать уровень доказательства.** Статусы: `SOURCE_REGISTERED` (источник найден); `SOURCE_REVIEWED` (содержание изучено); `OFFLINE_PASS` (автономный тест); `HISTORICAL_LIVE_REPORTED` (в источнике описан конкретный LIVE-прогон, без новой независимой проверки); `INSTALLED_READ_ONLY` (подключение/чтение); `LIVE_TEMPLATE_PASS` (реальный проход шаблона); `RELEASE_ACCEPTED` (полная приёмка и выпущенный `.tpl`). Эти статусы **не взаимозаменяемы**.
4. Соседний [снимок обнаруженных веток](OCTOBER_2026_GITHUB_BRANCH_SNAPSHOT.json) хранит все доступные на дату выборки ссылки и head SHA. Он служит **реестром обнаружения**, но не утверждением об аудите содержимого каждой ветки и не подтверждает дату каждого коммита.

## 2. Сводная матрица октябрьских исследований

| Код | Направление и исходные материалы | Что перенести в практику шаблона | Статус / запрет преувеличения |
|---|---|---|---|
| O26-01 | [База шаблона](./), [roadmap](TEMPLATE_BUILD_ROADMAP_v0.1.yaml), [предварительный checkpoint](CHECKPOINT_2026-10-06_PRELIVE.md) | Атрибуты, перья, линии, поверхности, материалы, классификация и свойства, виды и макеты, подготовка DWG/IFC, безопасность сборщика | Спецификации и код подготовлены; создание полного TPL и LIVE-строительство шаблона НЕ доказаны |
| O26-02 | [Проверка status gate 26.10](CHECKPOINT_2026-10-26_PREFLIGHT_STATUS_GATE.md), [CI на точном checkpoint HEAD](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/40351739041), [предыдущая CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/40351563256) | Исправленные PASS/BLOCKED статусы `inspect`/`plan`, exit code 2 при блокировке, восемь автономных регрессионных тестов | `OFFLINE_PASS`; последняя CI на `792f7d8` — SUCCESS. Windows `-Stage preflight` на действительном Archicad после исправления — NOT_RUN |
| O26-03 | [Реестр исследований APA](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results), [реестр находок 10.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/2026-10-10-research-register.md) | Происхождение GDL/Unicode, проёмы, roof/material, homeStory, Model Dump, систематические gates и receipts | Исторические результаты с разными состояниями PLN/портов не считать одним LIVE-прогоном |
| O26-04 | [Каталог расширений 18.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/CATALOG_20261018.md), [61-кандидатная оценка](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEED_EFFORT_AUDIT_20261018.md), [аудит TAPIR](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/TAPIR_VERSION_COMPATIBILITY_AUDIT_20261018.md) | Иерархия: штатные возможности AC29 → существующий APA/Tapir → готовый бесплатный компонент только под доказанный пробел | Каталог/рейтинг — SOURCE, не список установленных дополнений или проверенных скоростей |
| O26-05 | [Native whole-building PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74), [BUILD-01 issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) | Повторно применять существующие BIM Graph, DynamicCommands, SceneWriter, SQLite, GUID/BREP readback и зависимости host/openings; один writer | PR #74 сообщает конкретный исторический LIVE 21-элементной модели; универсальный новый BUILD-01 G0–G5 не принят, его нули не отменяют старые испытания |
| O26-06 | [Исследования native API и reuse, 07–08.10](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/working-archicad-mvp/docs/research) | Этажи, геометрия Roof/Shell/Slab, граф изменений, native MEP, SAF, спецификации, проверки количества, типовые узлы, контроль документации и выпущенных файлов | Десятки `architectural_ai_checkpoint_*` — архитектурное исследование, не автономная реализация всех механизмов |
| O26-07 | [План Rhino/Grasshopper R01 от 22.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/main/docs/apa-integration/INSTALL_AND_EVIDENCE_PLAN_R01_2026-10-22.md), [исследование openBIM/Grasshopper 08.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/working-archicad-mvp/docs/research/architectural_ai_checkpoint_38_openbim_semantic_and_parametric_orchestration_2026-10-08.md) | Rhino 8 + Grasshopper для сложной геометрии; Archicad 29 — хозяин нативной BIM-модели; автоматическая передача возможна только при проверенном соответствии типов/атрибутов/этажей/GUID | Сквозное AC29→GH→Rhino→AC29, гарантированное синхронное обновление и автоматический откат НЕ доказаны. Rhino требует самостоятельной действующей лицензии |
| O26-08 | [MEP исследование 08.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/working-archicad-mvp/docs/research/architectural_ai_checkpoint_39_mep_deep_research_cycles_and_audit_2026-10-08.md), [ограничения бесплатного расчёта](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/working-archicad-mvp/docs/research/architectural_ai_checkpoint_40_offline_license_free_engineering_2026-10-08.md) | Включить в методику требования к маршрутам, портам, соединениям и инженерным расчётам; не моделировать «условные» системы как проверенные | API-поддержка не доказывает корректность соединения или расчёта инженерной сети |
| O26-09 | [СПДС 2026](DOCUMENTATION_STANDARD_v0.1.md), [графика](GRAPHICS_STANDARD_v0.1.md), [DWG](DWG_TRANSLATOR_STANDARD_v0.1.md), [IFC](IFC_TRANSLATOR_STANDARD_v0.1.md) | Документацию ориентировать на принятый базис ГОСТ Р 21.101—2026 и ГОСТ 21.501—2018; переводчики и печать проверять на реальных выпускных артефактах | Готовый регистр/чертёжный сценарий не означает, что соответствие нормативам или PDF/DWG/IFC регрессионно принято |
| O26-10 | [Исследование BDD 125 элементов, PR #116](https://github.com/dvikt33-ux/safe-bim-layer/pull/116), [IFC-геометрия PR #170](https://github.com/dvikt33-ux/safe-bim-layer/pull/170), [AC30 read-only PR #110](https://github.com/dvikt33-ux/safe-bim-layer/pull/110) | Исторические evidence/receipts можно использовать для эталонных тест-кейсов, не перенося чужую геометрию и GUID в шаблон | Протоколы имеют собственные типы доказательств; PR #170 не заявляет native LIVE, AC30 не становится основной платформой |
| O26-11 | [AV-01 архитектурные согласованные виды, PR #65](https://github.com/dvikt33-ux/safe-bim-layer/pull/65) | Для любых видов и оформления одного здания использовать единую геометрию, согласованные планы, фасады, разрезы и проверку | Исследовательский/визуализационный принцип, не отдельная готовая BIM-функция |

## 3. Совместимость — конфликты, которые обязательно сохранять

- **Версия программы:** подтверждённая рабочая цель — **Archicad 29.2.1 (5101) RUS FULL** по [карточке среды](../ARCHICAD_RUNTIME_CURRENT.md). AC30 не заменяет её; перенос — самостоятельный будущий этап.
- **Версия TAPIR:** текущий [template-capability-matrix](template-capability-matrix-v0.1.yaml), [pin](tapir-version-pin-v0.1.yaml) и код сборщика опираются на сохранённую схему **1.5.8**. В документах APA указывается установленная **1.5.10**, но [аудит 18.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/TAPIR_VERSION_COMPATIBILITY_AUDIT_20261018.md) не нашёл публичного upstream-тега 1.5.10. Нельзя объявить 1.5.8 и 1.5.10 идентичными, автоматически обновлять расширение или подменять схему. Установленный APX, его SHA/регистрация команд требуют чтения на ПК.
- **Штатные возможности ≠ API:** пользовательский интерфейс Archicad с тиражированием, коллизиями, публикацией и осевыми сетками не доказывает наличие той же операции в текущем Tapir/MCP.
- **Массовые операции:** использовать существующий APA native copy/hotlink/SceneWriter, не создавать вторую систему записи и не повторять CREATE после неопределённого результата без reconciliation.
- **Rhino/GH:** официальный Live Connection для AC29/Rhino 8 — кандидат интеграции; совместимость конкретной установленной связки build 5101, точные типы и обратная синхронизация — отдельная приёмка; Rhino 9 и GH2 не основная конфигурация.
- **Лицензии/цена:** платный официальный MCP и ArchiFrame не включать в обязательный комплект; бесплатность MCP не отменяет лицензию Rhino/Archicad.
- **Качество:** отсутствие расхождений исходной модели, выпущенных документов и IFC/DWG подтверждать независимым readback, а не картинками.

## 4. Правила фактического использования для шаблона

**Включить сейчас на уровне знаний:** все источники в таблице и полный снимок веток, методики версий, нормативные и атрибутные спецификации, кандидаты готовых бесплатных решений, ограничения, предыдущие квитанции, негативные результаты.

**Не исполнять без дополнительных ворот:** live изменение проекта; обновление APX/версии TAPIR; установка Rhino/MCP; запись GDL, сложной крыши, сети MEP; экспорт как «готовый» выпуск; сохранение итогового TPL. Исходные файлы и исторические evidence не редактировать задним числом.

**Приоритет следующей работы именно по шаблону:**
1. На Windows подтвердить только чтение текущей среды, project identity, Tapir/schema и запуск `powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage preflight`; сохранить JSON/логи.
2. Только после `PASS` рассматривать санкционированные `core`, `materials-data`, `navigator-master` в новом чистом проекте; запрещено `--allow-nonempty` и обход `confirm-project`.
3. Проверить бумажное пространство, AutoText, Форму 3, PDF/DWG/IFC, библиотеки, шрифты, варианты View Map, Favorites, составные конструкции и матрицу сопряжений.
4. Отдельно выпустить `AC29_RU_SBIM_1.0.tpl` после приёмки и зафиксировать manifest/receipts; до этого статус **TPL_NOT_CREATED / RELEASE_NOT_ACCEPTED**.
5. Исследования Rhino/GH и универсального BUILD-01 продолжать как самостоятельные контуры; их прогресс не должен блокировать безопасный read-only preflight шаблона и не должен повышать его статус.

## 5. Контроль полноты источников

Инвентаризация охватила **все 244 ветки, возвращённые GitHub API в трёх страницах на 26.10.2026**. Файл `OCTOBER_2026_GITHUB_BRANCH_SNAPSHOT.json` сохраняет имена, HEAD SHA и предварительный признак тематической пригодности; **это не означает**, что содержимое всех 244 веток прочитано и все октябрьские коммиты каждой ветки сопоставлены. Отдельные работы вне данного репозитория, непушенные файлы и журналы Windows здесь не видны. Общее заявление «все октябрьские исследования полностью аудированы» было бы недостоверным.

Для окончательной сверки каждого источника необходимы `source branch/commit → original artifact → evidence scope → conflicts/superseded-by → template decision → status`; этот файл — единая точка входа и правила приёмки, а не отмена исходного APA Research Hub.

**Запрет:** не менять `main`, исходные PLN/PLА/APX, не переписывать исторические исследовательские отчёты и не выдавать SUCCESS GitHub Actions за исполнение Windows Archicad.
