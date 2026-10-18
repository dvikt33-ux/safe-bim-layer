# APA AC29 — действующая очередь, 18.10.2026 16Z

**Штаб:** [независимый аудит 16Z](hourly/review-20261018T16Z.md), 30 предметных проверок и два контрааудита. Детали: [01–10](hourly/audit-20261018T16Z-appendix-A.md), [11–20](hourly/audit-20261018T16Z-appendix-B.md), [21–30](hourly/audit-20261018T16Z-appendix-C.md).

**Прочитано:** №1 16Z blob 9f1d02ab, commit 2f515d65; №2 16Z blob 417f19de, commit b187942b. Канон PROJECT_PLAN.json revision182, 91 задач, только чтение: A11.S03 PARTIAL, A11.S08/S10 BLOCKED, A07.S03 READY. Реестр 61 кандидата. Предыдущая очередь blob db88a101 сохранена в истории Git.

## №1 — поиск готовых функций и библиотек

[Девять адресных тем F01–F09](hourly/audit-20261018T16Z-tasks-1.md): программный Multiply, IFC openings/ports, PDF физические анкеры, MEP wrapper, SAF converter, BCF viewer, STEP parser, Hotlink и исправление provenance PR159/PDF. Для каждой — версия, первоисточник, готовый контракт, лицензия, NOT_FOUND при отсутствии.

## №2 — поиск готовых способов подключения

[Десять цепочек I01–I10](hourly/audit-20261018T16Z-tasks-2.md): IfcDiff geometry/attributes, PR159→PR162→SceneWriter, безопасный IfcPatch, Publisher whitelist, BCF ZIP, Hotlink, PDF→hosted create, MEP, SAF, STEP validator. Предпочитать готовый adapter/wrapper/bridge, максимум три внешних звена. Никакой второй writer.

**Исправления аудита:** поздний LIVE PR159 подтверждён только на scratch PLN, не production; PR162 OFFLINE CI 12/12, LIVE не доказан. APA IfcDiff draft исключает geometry/attributes; обычный IfcDiff пропускает IfcFeatureElement. Publisher/IfcPatch/Split требуют защиты. Нет новых ACCEPTED, нет benchmark 100×.

**Правила:** SOURCE/OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED раздельно; исследование без установок, main, PLN/APX, кода и PR merge. MODEL_MODE_NOT_VERIFIABLE.