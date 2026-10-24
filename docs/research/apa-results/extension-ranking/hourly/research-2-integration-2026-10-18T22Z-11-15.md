# APA №2 22Z — проверки 11–15
SOURCE. Вопрос → источник/строка → контракт → вывод → следующий.

11. PDF paths и SHA? APA PR154 `scripts/apa_external_readonly.py` L16–26,35–44,138+: `pdfplumber=0.11.10`, SHA256, TOP-LEFT. REUSE; отдельно page/revision. Далее: hosted.
12. Метка равна проёму? APA PR160 `scripts/apa_ap2_massops_preflight.py` L1–15,22–25,75–90: `PDF_TEXT_MARK_ONLY`, page16, bboxPt. BLOCKED native create без host GUID/size/flip. Далее: DXF.
13. Есть DXF decoder? APA PR168 `scripts/apa_dxf_geometry_c1.py` L34–46,78–83: `recursive_decompose`, 50000 cap, unitConversionApplied=false. REUSE C1. Далее: MINSERT.
14. MINSERT раскрыт? ezdxf v1.4.5 `disassemble.py` L542–575: `mcount>1 → multi_insert()`; `entities/insert.py` L662–703: уникальные offsets, zero spacing collapses. REUSE, проверять координаты. Далее: C1 grouping.
15. C1 даёт per-cell assembly? PR168 L34–70: один `groups[digest].append` на parent, primitiveCount суммарный. NOT_FOUND per-cell; минимальный adapter в C1, не новый engine. Далее: XCLIP.

Источники: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py
https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py
https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py
