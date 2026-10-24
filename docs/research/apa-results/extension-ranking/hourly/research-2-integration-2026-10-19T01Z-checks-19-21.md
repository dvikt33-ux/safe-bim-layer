# APA №2 01Z — проверки 19–21: готовая QA и DXF
Источники: https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/validate.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py

19. Вопрос: JSON ошибок без своего движка? validate.py:91–100 `json_logger.statements` содержит `level/message/state`; `validate(file,logger,express_rules=False)`. REUSE, далее GUID.
20. Вопрос: ловит ли duplicate/invalid? validate.py:471–503 `used_guids`, `IfcRoot.UR1`, `validate_guid` проверяют дубли и base64; OFFLINE fixtures ещё нет. Далее DXF.
21. Вопрос: раскрывается ли MINSERT в APA? C1:34–50 `recursive_decompose([parent])`; WCS primitives в paths. SOURCE да, но assembly count отдельно. Далее upstream mcount.
