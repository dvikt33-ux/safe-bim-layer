# APA №1 — два независимых контрааудита, 2026-10-19 01Z

## А. Первоисточники, версии, лицензии, совместимость

1. **DevKit:** все 27 проверенных методов/полей относятся к официальному тегу `GRAPHISOFT/archicad-api-devkit:29.3100`, а не текущей странице Doxygen, где отображается SDK30. Методы имеют точные строки и ссылки в трёх приложениях.
2. **Лицензия:** `GRAPHISOFT/archicad-api-devkit/LICENSE`, blob `1e1ec1f4281838ffc8f30293ad5827276f87aa4a`, — Graphisoft Software License Agreement, не MIT. Метаданные `GSMObject::GetLicense` не являются автоматическим юридическим разрешением.
3. **Библиотеки:** `Library::GetPackageDependencies` возвращает name, package ID, subversion; не устанавливает зависимости. `GetPackageMinACVersion` и `GetPackageMinACBuildNumber` — метаданные, не runtime acceptance.
4. **MEP:** `VentilationPortDefault::Modifier::SetShape` и `RoutingSegmentDefault::Modifier::SetCrossSectionShape` подтверждены. Но `TransitionDefault::Modifier` документирует `SetAngle/SetPreferenceTable`, не доказан setter двух разных портов. Круг→прямоугольник **NOT_VERIFIED**.
5. **SAM:** `ACAPI_Analytical_CreateAnalyticalLoadCase(API_AnalyticalLoadCase&)` существует, хотя описание Doxygen ошибочно называет его созданием Load Group. Доверять сигнатуре, не заголовку.
6. **IfcOpenShell 0.8.5:** `validate.py` строки 471–503 содержит `used_guids` и проверку `IfcRoot.UR1`; прежний баг-репорт о дубликатах не отражает этот код. Лицензия Python LGPL-3.0-or-later.
7. **ifcbench:** `pyproject.toml` version 0.0.1 и Python >=3.10, GitHub repository license=null, LICENSE отсутствует в корне; `runner.py:29–33` hardcodes `bin/python` вместо Windows `Scripts/python.exe`. Windows-ready **NO** для этой версии без внешних изменений.
8. **Tapir:** установленная 1.5.10 не отождествляется с upstream 1.5.9/1.7.1. Локальный JSON contract и бинарная подпись NOT_VERIFIED. Не выполнять native writes.

**Итог А:** SOURCE=30/30; Windows/ABI/installed не проверены; выявлены SDK docs typo, POSIX-only path, неопределённая лицензия ifcbench и отсутствие доказанного mixed-transition setter.

## Б. Инженерная польза, отсутствие дубликатов и ограничения

1. `CloneNativeGroupV1` уже есть. Не создавать второй Group/Multiply writer.
2. PR #154/#160 покрывают PDF vectors и preflight marks; новая библиотечная инвентаризация решает другую задачу — .libpack dependencies и GDL provenance.
3. PR #159/#162 покрывают native group-first; `LibraryManager` дополняет их проверкой source library, но не гарантирует hosted placement.
4. PR #167/#170 дают IFC port/geometry; SDK29 Transition/Port — нативный слой, но он не разрешает A11.S10 без qualified circular/rectangular transition и сохранения GUID.
5. `ACAPI_Analytical_CreateLoad*` позволяет описать группы/случаи/сочетания, но **не** подтверждает SAF artifact, solver, нагрузки СП; канон A11.S08 остаётся BLOCKED.
6. `ifcopenshell.validate` уже содержит GlobalId duplicate QA: повторно писать checker не нужно; IFC GlobalId != Archicad GUID.
7. `ifcbench` отличается от Native Model Dump межверсионным сравнением tessellation/kernel, но 0.0.1 не готов к Windows и не имеет подтверждённой лицензии. Не заявлять ускорение.
8. SDK29 `group___publisher.html` посвящён регистрации дополнительных форматов (SaveProc), **не** доказательство программного PublishPublisherSet. Tapir upstream PublishPublisherSet и установленная 1.5.10 — разные уровни.

**Итог Б:** 6 карточек: 5 переиспользуют SDK29/IfcOpenShell, 1 условный ifcbench; новых ACCEPTED нет. A11.S03 PARTIAL, A11.S08/A11.S10 BLOCKED, A07.S03 READY. Рейтинги — экспертные, benchmark=NOT_MEASURED. Никаких изменений main, PLN, APX, кода, PROJECT_PLAN.json rev182 или NEXT_RESEARCH_PRIORITIES.md.
