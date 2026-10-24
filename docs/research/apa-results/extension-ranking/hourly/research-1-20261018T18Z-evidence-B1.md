# APA AC29 — проверки 16–23 (18Z)
Отдельные первичные факты, не локальные тесты. Продолжение [01–15](research-1-20261018T18Z-evidence-A.md).

16. **SAF импорт.** NuGet StructuralAnalysisFormat **1.7.3** README lines 207–215: `IExcelImportService`, `Import(Stream)`, возвращает `ExcelModel`. Источник: https://www.nuget.org/packages/StructuralAnalysisFormat/1.7.3 . Контроль: формат XLSX, не FEM solver, runtime не проверен.
17. **SAF экспорт.** Там же lines 220–226: `IExcelExportService.Export(Stream, ExcelModel)`. Готовый writer Excel, но lossless 6DOF/LCS/loads не доказан.
18. **SAF bootstrap.** Там же lines 143–149, 169–172: `StructuralAnalysisFormat.Bootstrappers.SimpleInjector4/5`, `IBootstrapper.CreateScope()`. Нельзя утверждать, что основной пакет сам обеспечивает DI.
19. **SAF зависимости.** NuGet 1.7.3: `.NETStandard2.0`; `EPPlus>=4.5.3.3`, `FluentValidation>=10.2.3`, `UnitsNet>=4.72.0`. Знак >= означает, что версии не зафиксированы; лицензии проверить по фактическому lockfile.
20. **SAF лицензионный риск.** Производитель EPPlus: v4 LGPL, v5+ Polyform Noncommercial/коммерческая. Источник: https://www.epplussoftware.com/en/Home/LgplToPolyform . Apache-2.0 главного SAF пакета не покрывает автоматически все транзитивные зависимости.
21. **IFC2X3 геопривязка.** Исходник `IfcOpenShell@v0.8.0` `geolocation.py:214–239`: `get_helmert_transformation_parameters()` читает `IfcProject.ePSet_MapConversion`. Источник: https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.8.0/src/ifcopenshell-python/ifcopenshell/util/geolocation.py . **ВНИМАНИЕ:** ref v0.8.5 не найден; installed 0.8.5 API НЕ подтверждён.
22. **IFC4 геопривязка.** Тот же файл: `IfcCoordinateOperation`, `IfcMapConversion`, `IfcMapConversionScaled`, `IfcRigidOperation`. PR165 `_ifc_georef` перечисляет `IfcMapConversion` и CRS, не выполняет roundtrip.
23. **Отсутствие georef.** `auto_xyz2enh()` в том же файле lines 147–179 возвращает входные XYZ, когда Helmert parameters отсутствуют. Тождество НЕ означает, что координаты геодезически проверены.

Гейты: SOURCE=VERIFIED_FOR_LISTED_VERSION; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_CHECKED; LIVE=NOT_RUN; ACCEPTED=NO.
