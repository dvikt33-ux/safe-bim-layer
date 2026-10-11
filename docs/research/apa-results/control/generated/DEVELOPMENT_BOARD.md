# APA — разработка продукта / DEVELOPMENT_BOARD

Generated from [PROJECT_PLAN.json](../PROJECT_PLAN.json); this is not a second register.
Source of truth: task statuses and evidence in PROJECT_PLAN.json.
P/A completion is computed; DONE_PUBLISHED requires **every** child S-ID DONE_PUBLISHED.
requires_approval tasks are not dispatchable until separate owner approval is recorded.

## Краткая сводка

- План: APA-P70 — Разработка APA — полный цикл проектирования и выпуска
- Статус: **READY**; завершено 0/23 подзадач.
- Сейчас: не выполняется; нет IN_PROGRESS.
- Следующая доступная: APA-P70.A01.S01 — Сопоставить полный продуктовый контракт с существующим кодом и исследованиями

## Этапы → задачи

| Задача | Состояние | Выполнено подзадач |
| --- | --- | ---: |
| APA-P70.A01 — Единая база существующих возможностей и доказательств | READY | 0/3 |
| APA-P70.A02 — Требования, нормативы и библиотека конкретного проекта | WAITING | 0/3 |
| APA-P70.A03 — Планировка и редактируемая нативная BIM-модель | WAITING | 0/3 |
| APA-P70.A04 — Конструктивные узлы, кладка, фасады и сопряжения | WAITING | 0/3 |
| APA-P70.A05 — Расчёт несущих систем и инженерная обратная связь | WAITING | 0/3 |
| APA-P70.A06 — MEP и междисциплинарная координация | WAITING | 0/2 |
| APA-P70.A07 — Ведомости, чертежи, нормативная проверка и выпуск | WAITING | 0/3 |
| APA-P70.A08 — Сквозная приёмка и расширение без переписывания ядра | WAITING | 0/3 |

## Подзадачи и следующий шаг

### APA-P70.A01 — Единая база существующих возможностей и доказательств

- **APA-P70.A01.S01 [READY / ELIGIBLE]** Сопоставить полный продуктовый контракт с существующим кодом и исследованиями; исследования: APA-P50.A01.S01, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-PR16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md), [ART-APA-LIVE-SCRATCH-PARTIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md)
- **APA-P70.A01.S02 [READY / WAITING_DEPS]** Привязать все значимые наработки к функциям продукта, выявить пробелы; зависимости: APA-P70.A01.S01, APA-P50.A01.S01; исследования: APA-P50.A01.S01, APA-P50.A02.S01
  - Источники/ветки: [ART-REGISTER](../../../../../docs/research/apa-results/ARTIFACT_REGISTER.md), [ART-TRACE-REPORT](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-110048Z-legacy-traceability/REPORT.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)
- **APA-P70.A01.S03 [READY / WAITING_DEPS]** Утвердить минимальные границы интеграции и порядок сквозных поставок; зависимости: APA-P70.A01.S01; исследования: APA-P50.A01.S01, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)

### APA-P70.A02 — Требования, нормативы и библиотека конкретного проекта

- **APA-P70.A02.S01 [READY / WAITING_DEPS]** Собрать семантический контракт задания, участка, этажей и помещений; зависимости: APA-P70.A01.S03; исследования: APA-P10.A01.S02, APA-P10.A02.S02, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)
- **APA-P70.A02.S02 [READY / WAITING_DEPS]** Связать проектные требования с версиями нормативов и проверяемыми правилами; зависимости: APA-P70.A02.S01; исследования: APA-P10.A01.S02, APA-P10.A02.S02, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md)
- **APA-P70.A02.S03 [READY / WAITING_DEPS]** Собрать проектный Library Pack из проверяемых строительных систем и узлов; зависимости: APA-P70.A02.S01, APA-P70.A01.S03; исследования: APA-P10.A01.S02, APA-P10.A02.S02, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12), [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)

### APA-P70.A03 — Планировка и редактируемая нативная BIM-модель

- **APA-P70.A03.S01 [READY / WAITING_DEPS]** Связать помещения, несущую схему, оси, уровни и конструктивные ограничения; зависимости: APA-P70.A02.S03; исследования: APA-P10.A01.S02, APA-P10.A01.S03, APA-P10.A03.S01, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md)
- **APA-P70.A03.S02 [READY / AWAITING_APPROVAL]** Собрать модель средствами уже существующих BIM-исполнителей; зависимости: APA-P70.A03.S01; исследования: APA-P10.A01.S02, APA-P10.A01.S03, APA-P10.A03.S01, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-PR16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-APA-ASSEMBLY-PLAN](../../../../../docs/research/apa-results/control/APA_ASSEMBLY_INTEGRATION_PLAN.md), [ART-APA-LIVE-SCRATCH-PARTIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md)
- **APA-P70.A03.S03 [READY / WAITING_DEPS]** Доказать редактируемость, GUID/host/story/material и инкрементальное обновление; зависимости: APA-P70.A03.S02; исследования: APA-P10.A01.S02, APA-P10.A01.S03, APA-P10.A03.S01, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-REUSE-NATIVE-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-HIGHLEVEL-PR34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34), [ART-APA-LIVE-SCRATCH-PARTIAL-20261011](../../../../../docs/research/apa-results/runs/2026-10-11/apa-p70-a03-live-scratch-partial-slab-reconciliation.md)

### APA-P70.A04 — Конструктивные узлы, кладка, фасады и сопряжения

- **APA-P70.A04.S01 [READY / WAITING_DEPS]** Вывести из модели обязательные семейства узлов и их условия применимости; зависимости: APA-P70.A03.S01; исследования: APA-P10.A02.S02, APA-P10.A01.S03, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-CSE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_24_construction_systems_detail_first_selection_2026-10-08.md), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12)
- **APA-P70.A04.S02 [READY / WAITING_DEPS]** Привязать выбранные узлы и композиции к нативным BIM элементам; зависимости: APA-P70.A04.S01, APA-P70.A03.S02; исследования: APA-P10.A02.S02, APA-P10.A01.S03, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md)
- **APA-P70.A04.S03 [READY / WAITING_DEPS]** Проверить узлы окон, облицовки, перекрытий и кровельных примыканий; зависимости: APA-P70.A04.S02; исследования: APA-P10.A02.S02, APA-P10.A01.S03, APA-P50.A02.S01
  - Источники/ветки: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-DETAILS-V212](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/project-accelerator-integration-pr-20261009/details/releases/v2.12)

### APA-P70.A05 — Расчёт несущих систем и инженерная обратная связь

- **APA-P70.A05.S01 [READY / WAITING_DEPS]** Получить проверяемую расчётную схему и исходные нагрузки; зависимости: APA-P70.A03.S01, APA-P70.A02.S02; исследования: APA-P10.A01.S01, APA-P10.A03.S01, APA-P10.A03.S02
  - Источники/ветки: [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
- **APA-P70.A05.S02 [READY / WAITING_DEPS]** Использовать SAM/SAF/IFC и доступный проверенный расчётный движок; зависимости: APA-P70.A05.S01, APA-P70.A03.S02; исследования: APA-P10.A01.S01, APA-P10.A03.S01, APA-P10.A03.S02
  - Источники/ветки: [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)
- **APA-P70.A05.S03 [READY / WAITING_DEPS]** Применить результаты инженерного расчёта и повторно проверить узлы; зависимости: APA-P70.A05.S02, APA-P70.A04.S02; исследования: APA-P10.A01.S01, APA-P10.A03.S01, APA-P10.A03.S02
  - Источники/ветки: [ART-APA-STRUCTURAL-HANDOFF](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_36_structural_handoff_accelerator_architecture_2026-10-08.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md)

### APA-P70.A06 — MEP и междисциплинарная координация

- **APA-P70.A06.S01 [READY / WAITING_DEPS]** Сформировать инженерные требования и трассы на базе штатного MEP; зависимости: APA-P70.A03.S02, APA-P70.A02.S02; исследования: APA-P10.A02.S04, APA-P10.A02.S03
  - Источники/ветки: [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md)
- **APA-P70.A06.S02 [READY / WAITING_DEPS]** Проверить инженерные сети, проходки, коллизии и узлы пересечений; зависимости: APA-P70.A06.S01, APA-P70.A04.S02; исследования: APA-P10.A02.S04, APA-P10.A02.S03
  - Источники/ветки: [ART-MEP-SOURCE-20261010-PORTGRAPH](../../../../../docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md)

### APA-P70.A07 — Ведомости, чертежи, нормативная проверка и выпуск

- **APA-P70.A07.S01 [READY / WAITING_DEPS]** Получить согласованные планы, разрезы, фасады, спецификации и узлы; зависимости: APA-P70.A03.S03, APA-P70.A04.S02; исследования: APA-P10.A02.S03, APA-P10.A01.S03, APA-P50.A01.S03
  - Источники/ветки: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-PLP-CONTRACT](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/project-library-pack-contract-v0.1.yaml)
- **APA-P70.A07.S02 [READY / WAITING_DEPS]** Выполнить поэлементную и общепроектную проверку нормативов; зависимости: APA-P70.A07.S01, APA-P70.A05.S03, APA-P70.A06.S02; исследования: APA-P10.A02.S03, APA-P10.A01.S03, APA-P50.A01.S03
  - Источники/ветки: [ART-APA-RU-JUNCTION-NORMS](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_29_russian_junction_norms_2026-10-08.md), [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md)
- **APA-P70.A07.S03 [READY / WAITING_DEPS]** Собрать итоговый пакет BIM/IFC/PDF и доказательства проверки; зависимости: APA-P70.A07.S02; исследования: APA-P10.A02.S03, APA-P10.A01.S03, APA-P50.A01.S03
  - Источники/ветки: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-FULL-CYCLE-RESEARCH](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_37_global_project_library_story_lira_fullcycle_2026-10-08.md)

### APA-P70.A08 — Сквозная приёмка и расширение без переписывания ядра

- **APA-P70.A08.S01 [READY / AWAITING_APPROVAL]** Проверить полный цикл создания проекта на эталонном ИЖС; зависимости: APA-P70.A07.S03; исследования: APA-P50.A01.S01, APA-P50.A03.S01, APA-P50.A03.S02
  - Источники/ветки: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md), [ART-APA-PR16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16)
- **APA-P70.A08.S02 [READY / AWAITING_APPROVAL]** Проверить доработку единственного открытого существующего PLN; зависимости: APA-P70.A08.S01; исследования: APA-P50.A01.S01, APA-P50.A03.S01, APA-P50.A03.S02
  - Источники/ветки: [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
- **APA-P70.A08.S03 [READY / WAITING_DEPS]** Доказать расширяемость на другом типе здания и системах; зависимости: APA-P70.A08.S02; исследования: APA-P50.A01.S01, APA-P50.A03.S01, APA-P50.A03.S02
  - Источники/ветки: [ART-APA-FAST-COMPILER](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/research/architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md), [ART-APA-FULL-CYCLE](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/project-accelerator-integration-pr-20261009/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md)
