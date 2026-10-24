# APA №1 — два независимых повторных контрааудита, 19.10.2026 00Z

## Контрааудит A — первичность, версии, лицензии

1. Официальный сайт Graphisoft сейчас показывает **Archicad 30 C++ API** даже на ранее индексированных страницах с заголовком Archicad 29. Прямой Opera readback новой вкладки подтвердил «Archicad 30». Поэтому 20+ native-утверждений перепроверены не по живому сайту, а по `GRAPHISOFT/archicad-api-devkit` **tag 29.3100**: Doxygen HTML blob DesignOptionManager `feab8e4c2ebb2dc94f571cc67946119519d40cb9`, Analytical `1cb66ecdbe9a64c47ee1ae0cbd0d47256265e6bf`, HookManager `73274106eac97180a7ae5a55e03091b7cd774da7`, PhysicalSystem `c8cccaacfc81ee61cf3c8d5568a4a30430390103`. SDK29 tag is pinned; локальный AC29 build5101 ABI NOT_VERIFIED.
2. Graphisoft SDK29 LICENSE blob `1e1ec1f4281838ffc8f30293ad5827276f87aa4a` — **проприетарная EULA**, запрет распространять DevKit как продукт и републиковать документацию. Это не MIT/GPL. Ссылки на оригиналы допустимы, копировать SDK в APA без правовой оценки нельзя.
3. buildingSMART IDS-Audit-tool: README blob `b3419d70f290377ce7639f9737c319d3d6596fe5`, LICENSE MIT `437772b8f202c2238235f1834f606f7fd867042e`, CLI csproj `aba0c3a834e29a42948eaaadf4029ed464497d74`, lib csproj `393447e47a34709454cff02df9d9fb9aa073edf2`. Version **1.0.124** в исходнике; NuGet/installed package SHA не проверен. IDS standard XSD version 1.0.0 из `buildingSMART/IDS` branch development; LICENSE **CC BY-ND 4.0** (не MIT), не путать лицензию программы и стандарта.
4. IfcOpenShell source pinned tag `ifcopenshell-python-0.8.5`, Ifc2Sql blob `d1405e9a334905bacb74bd1333d043553c87f45c`, geolocation `47c8886691a5c14d887d4ebcfd4b9c12b7bc08c9`; source headers LGPL-3.0-or-later. Никаких заявлений о Python wheel 1.5.10 Tapir, локальной установке или тестах.
5. Источники UI vs SDK строго различены; CURRENT Graphisoft website AC30 не использован как доказательство AC29. Одна свежая вкладка Opera успешно открыта, прочитана и закрыта, пользовательские 334+ вкладки не закрывались.

## Контрааудит B — инженерная полезность, дублирование и критерии

1. Канон `PROJECT_PLAN.json` rev182 blob `c2ab2f9d606db1412c4031076103c267fc463f83`, 91 задач: A11.S08 (SAF) и A11.S10 (MEP переход) **BLOCKED**, A11.S03 PARTIAL, A07.S03 READY. Read-only native SAM не означает SAF export/solver/нагрузки по СП. Native PhysicalSystem не означает размерный transition.
2. 61-кандидатный каталог blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9` не содержит отдельного DesignOptions, official IDS Audit, Ifc2Sql, PhysicalSystem. IfcOpenShell и IFC QA уже есть, поэтому геопривязка — углубление существующего, не новый parser. Матрица рейтинга не benchmark.
3. PR #154 PDFVectors (head ca28e9b8), #159 group acceptance (f13b1dcd), #160 PDF→OpenBIM (e8cbbf97), #162 group-first CloneNativeGroupV1 (f7c37b84), #170 IFC OBJ/GLB bounds (35a8b7b2), #171 Hotlink single LIVE (b3a37324), #173 batch Hotlink historical LIVE-02 (eee14936) прочитаны через GitHub PR metadata/body. Новые native Design Options и SAM не повторяют эти маршруты. Никаких новых LIVE тестов.
4. Ifc2Sql `should_expand=True` отменяет уникальность ifc_id; default `full_schema=True` и `should_get_geometry=True` потенциально затратны. Запись отдельной SQL базы допустима только в будущем OFFLINE на копии. Не выдавать SQL snapshot за новый Router или способ ускорения.
5. IDS Audit Tool валидирует **файл требований IDS**, IfcTester проверяет **модель IFC по IDS**. Пропуск семантической проверки (`--omitContent`) не должен давать ACCEPTED. Native IFC relationship data — экспортная структура, не read-only inventory.
6. Кандидаты отобраны за реальное непокрытое поведение, а не за количество функций. 7 карточек с проверяемыми gates переданы №2; внедрение не выполнялось.

**Статусы:** SOURCE=29 distinct contract checks; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_CHECKED; LIVE=NOT_RUN; ACCEPTED=NO. MODEL_MODE_NOT_VERIFIABLE. Измеренного ускорения нет.
