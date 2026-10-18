# APA AC29 — аудит 16Z, часть A (01–10)

Выполнено 10 независимых сверок. Канонический план revision182/91 задач, blob c2ab2f9d; №1 16Z blob 9f1d02ab (commit 2f515d65, 16:06:50Z), №2 16Z blob 417f19de (commit b187942b, 16:29:20Z).

01 VERIFIED: план A11.S03 PARTIAL, A11.S08/S10 BLOCKED, A07.S03 READY. Поручение: не повышать без квитанций.
02 VERIFIED: матрица 61 кандидата; баллы экспертные, не benchmark. Не дублировать IfcOpenShell.
03 VERIFIED: оба отчёта 16Z существуют. №1 PDF пункты 26–27 без воспроизводимых SHA/анкеров; №2 C2/C3 поверхностны. Восстановить.
04 CORRECTED: PR159 body старый NOT_LOCALLY_EXECUTED, но поздний комментарий #6244465302 сообщает LIVE. Читать квитанции.
05 VERIFIED: bridge reconciliation blob 645ab697, 36→44 GUID: 4 Column + 4 ColumnSegment; два клона на 15/30 м. Считать детей.
06 LIVE_SCOPED: bridge resume-v2 blob 37591302, Move/Ungroup/Save PASS, source SHA unchanged; только scratch PLN/19724. Не production.
07 OFFLINE_PASS: PR162 job117562030135 8/8 OK; job117564434530 12/12 OK. Не считать LIVE.
08 VERIFIED: group_strategy blob153bc1e3 использует Create/CloneNativeGroupV1, nativeWritePermission=false. Единственный SceneWriter.
09 VERIFIED: PR160 hosted openings нельзя generic copy; PDF label center не physical anchor. Искать host/контур.
10 SOURCE: PR154 PDFVectors Bézier/cp1251, installed-router acceptance pending. Не объявлять INSTALLED.

Источники: https://github.com/dvikt33-ux/safe-bim-layer/pull/159 ; https://github.com/dvikt33-ux/safe-bim-layer/pull/162 ; https://github.com/dvikt33-ux/safe-bim-layer/pull/160 ; https://github.com/dvikt33-ux/safe-bim-layer/pull/154 ; https://github.com/dvikt33-ux/safe-bim-bridge/tree/feature/apa-ac29-apx-build-mailbox-20261018/safe-bim-mailbox/apa-ac29-group-acceptance/results

Контрааудит A: старое «LIVE NOT_FOUND» ошибочно, но live только scratch. PDF/BCF/IFC источники не равны локальной установке. MODEL_MODE_NOT_VERIFIABLE.