# APA AC29 №2 17Z — source evidence 11–20

10 последовательных проверок кода PR165/V1, SOURCE only; никакие скрипты не запускались.

11. **DXF INSERT** [L259-L278](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L259-L278) — insert/xscale/yscale/zscale/rotationDegrees, attribs[:40], transformsApplied=false; MINSERT row_count/column_count не развёрнут. **Вердикт/следующий вопрос:** ADAPTER для OCS/array; MINSERT fixture.

12. **DXF TEXT/MTEXT** [L281-L295](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L281-L295) — rawText, insert, style, ocrPerformed=false. **Вердикт/следующий вопрос:** не physical opening anchor; font/codepage fixture.

13. **DXF DIMENSION** [L298-L315](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L298-L315) — dimtype/textOverride/defpoint/geometry, geometryOrScaleRecalculated=false. **Вердикт/следующий вопрос:** не авторитетный размер; измерить по геометрии.

14. **Входной guard** [L55-L61](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L55-L61) — resolve(strict=True), suffix .ifc/.dxf, MAX_SOURCE_BYTES=4GiB. **Вердикт/следующий вопрос:** 4GiB disk не лимит 48GB RAM; peak RSS fixture.

15. **Output guard** [L64-L74](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L64-L74) — новый .json вне stable APA, not p.exists(); позже open('x'). **Вердикт/следующий вопрос:** exclusive create; проверить partial-output.

16. **Truncation** [L76-L80](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L76-L80) — SAMPLE_LIMIT=5000; total/items/truncated. **Вердикт/следующий вопрос:** items не полный граф; проверить manifest.

17. **Версии V1** [L20-L27](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_readonly.py#L20-L27) — ifcopenshell/ifcdiff/ifctester/ifcclash=0.8.5, ezdxf=1.4.5. **Вердикт/следующий вопрос:** pin в коде не installed; doctor/readback.

18. **Runtime V2** [L328-L349](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L328-L349) — Windows V1/venv/Scripts/python.exe, installation.json и 3 SHA256. **Вердикт/следующий вопрос:** REUSE V1, V2 не installed; проверить receipt.

19. **Subprocess** [L352-L382](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L352-L382) — argv list, timeout=1200, script hash before/after, report <200MiB после записи. **Вердикт/следующий вопрос:** нет peak-memory gate; crash/partial/source-race fixtures.

20. **Router** [L18-L59](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_entrypoint_v2.py#L18-L59) — V1 six first, +12 local-python, reviewed_read_only=True; exact a/output. **Вердикт/следующий вопрос:** REUSE original DynamicCommands; catalog hash/offline tests.

Upstream независимая сверка: https://ezdxf.readthedocs.io/en/stable/blocks/insert.html (MINSERT row_count/column_count); https://ezdxf.readthedocs.io/en/stable/concepts/units.html ($INSUNITS и block units). PR165 acceptance: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/docs/research/apa-results/extension-ranking/FEATUREPACK_V2_ACCEPTANCE.md. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED не подтверждены.
