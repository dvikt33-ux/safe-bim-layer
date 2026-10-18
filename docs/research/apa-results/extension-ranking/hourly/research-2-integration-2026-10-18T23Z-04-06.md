# Проверки 04–06 — APA V2/B2

04. **Доказана ли нативная связь MEP?** PR165 строки 170–190: `IfcRelConnectsPorts`, `unlinkedByIfcRelConnectsPorts`, `nativeMEPConnectionVerified=False`. Вердикт только IFC QA; далее сверить native.

05. **Нужен ли новый Router?** PR165 строки 381–405: `router.add_local_provider`, `review_policy(...READ_ONLY)`. Вердикт REUSE; далее B2.

06. **Есть ли готовые IFC артефакты?** PR167 строки 20–24: `IFCCSVExport, IFCExtractElements, IFCBCFIssues`. Вердикт не дублировать; далее проверить версию.

Источники: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py
https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-artifacts-b2-20261018/scripts/apa_ifc_artifacts_b2.py
