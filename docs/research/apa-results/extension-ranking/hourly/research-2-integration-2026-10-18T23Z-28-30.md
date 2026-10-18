# Проверки 28–30 — license и SDK29

28. **Лицензия BCF3?** pinned `src/bcf/pyproject.toml:21–24` классификатор GPLv3, общий IfcOpenShell README называет bcf LGPL3+. Вердикт LEGAL_NOT_VERIFIED; BCF3 defer.

29. **Нативный Issue inventory?** Graphisoft SDK29 `ACAPI_Markup_GetList(APINULLGuid,&list)`, `ExportToBCF(fileLoc,ids,useExternalId,alignBySurveyPoint)`. Вердикт C++ SOURCE; готовый APA JSON binding NOT_FOUND. Далее sample/ABI.

30. **PDF→BIM?** SDK29 `ACAPI_Markup_ImportFromPDF(fileLoc,silentMode,openPalette)`, Since AC29, APIERR_BADNAME для стороннего PDF. Вердикт только импорт замечаний, не чертежей; LIVE запрещён.

Источники: https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/bcf/pyproject.toml
https://graphisoft.github.io/archicad-api-devkit/group___markup.html
