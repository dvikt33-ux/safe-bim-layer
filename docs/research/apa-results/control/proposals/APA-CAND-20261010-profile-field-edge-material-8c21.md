# TASK_PROPOSAL_V1 — проверка проекции полей профилей и материалов кромок

```yaml
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-20261010-profile-field-edge-material-8c21
origin: technical
proposer_run_id: apa-tech-20261010T153651Z-stories-attributes-8c21
source_substep_id: APA-P10.A01.S02
proposed_parent_plan: APA-P20
proposed_action: APA-P20.A01
suggested_substep_id: APA-P20.A01.S05
work_key: profile-field-projection-edge-material-readback
title: Read-only parity GetProfiles fields/skinOutlines and per-edge Building Material
kind: VALIDATION
priority: 1
depends_on: [APA-P20.A01.S02]
related: [APA-P10.A01.S02, APA-P20.A01.S03]
inputs: [ART-REGISTER]
outputs: [read-only profile field matrix, per-edge material parity log, negative-case evidence]
acceptance: "На неизменяемом тестовом PLN read-only GetProfiles с fields omitted, skins, skinOutlines, skins+skinOutlines; документировать точный результат, число hatch/outline/arc/edge и GUID материалов, сверить с независимым native readback, не путать profile skin/edge с face material. PASS только при подтвержденной полноте, FAIL при воспроизводимом расхождении; отсутствие native эталона NOT_VERIFIED."
requires_approval: false
expected_mvp_benefit: "Исключить потерю контуров профиля и edge-level материалов в MVP, не писать новый native resolver без доказанного пробела."
evidence_urls:
  - https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L1827-L1833
  - https://github.com/ENZYME-APD/tapir-archicad-automation/blob/02691b5d680b60c73317e8e49b78ab14dfd4c9d8/archicad-addon/Sources/AttributeCommands.cpp#L1903-L1975
  - https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___profile_attr_type.html
risks: "Tapir 1.7 upstream != installed custom 1.5.10; read-only LIVE not done; may overlap generic SDK coverage, auditor must verify work_key/acceptance and dependency DAG."
```

## Доказанная по исходному коду причина

В Tapir 1.5.9 и 1.7.0 `skinOutlines` указан в `GetProfiles.fields`, но отсутствует в `wantsGeometryDerivedFields` и вложен в ветку `Wants("skins")`. Следовательно, запрос **только** `fields:["skinOutlines"]` не достигает `outlineCoords`/ `outlineSubPolyEnds`/ `outlineArcs`. Рабочий source-level обход: запрашивать `["skins","skinOutlines"]` или не указывать `fields`. Это вывод из C++ ветвления, не LIVE тест.

Кроме того, `ForEachProfileEdge` сериализует собственный `buildingMaterialId` кромки; он может отличаться от `skin.buildingMaterialId`. Необходимо отдельно сверять edge materials. Raw profile vector geometry целиком GetProfiles не обещает.

## Решение аудитора — PENDING_AUDIT

Не добавлять в `PROJECT_PLAN.json` до независимой проверки: актуального каталога S-ID/work_key, подтверждённой нужности отдельного шага (вместо расширения существующего), зависимостей, возможности read-only теста, GitHub CAS/readback и controller CI. Учитывать ранее предложенный `APA-P20.A01.S04` (Opening geometry) — это **другая** задача, не занимать её ID.
