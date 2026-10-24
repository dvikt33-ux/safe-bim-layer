# APA AC29 / Исследователь №1 — доказательства 01–15 (20261018T18Z)
Исследование готовых решений, без установки, выполнения кода и изменений модели. Каждая строка — отдельная проверка определённого факта по прочитанному первоисточнику, не тест в AC29. SOURCE означает документ/исходник, не локальную работоспособность.

| № | Вопрос и первоисточник | Точное свидетельство | Вывод и внутренний контроль |
|---|---|---|---|
| 01 | Канонический план: `research/apa-verified-results-hub-20261010:docs/research/apa-results/control/PROJECT_PLAN.json` | Blob `c2ab2f9d606db1412c4031076103c267fc463f83d`, JSON `revision:182`, `tasks` | План существует, читать только; статусы не повышались. |
| 02 | Реестр 61 кандидата: `research/apa-extension-ranking-hub-20261018:docs/research/apa-results/extension-ranking/candidates.json` | Blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`, `total:61`; нет имен `occt-import-js` и `BCF.js` | Это новые ИМЕННЫЕ кандидаты относительно реестра, не доказательство отсутствия аналогичной функции в APA. |
| 03 | PR164: причина остановки `scripts/apa_ac29_group_scenewriter_reconcile_readonly.py` | Строки 146–151: `GetAddOnVersion` ожидает 1.5.10, старый каталог `tapir-1.5.8.json` сообщает 1.5.8; 172–174 фиксируют drift; blob `e6641ba84f3eccc86a370b3c73ab644f3586ad9e` | Существует готовый read-only reconcile; НЕ искать второй group writer и не перезапускать writer до устранения provenance. Данные из исходника, текущий LIVE не выполнялся. |
| 04 | PR165 `scripts/apa_high_density_readonly_v2.py` | Строки 24–36 перечисляют 12 команд: 8 IFC и 4 DXF; blob `39b8b60474bd31607c126f764cc167438ace7d7e` | Прямое дублирование их инвентаризаций запрещено; искать только недостающие свойства. |
| 05 | PR165 новая квитанция установленного smoke | `V2_INSTALLED_SMOKE_RECEIPT_20261018.json`, blob `92c664eff07848e8bd74b9a414be8bc331c0b210`: 12 записей PASS, `fixtureKind:SYNTHETIC_IFC4_DXF`, `nativeCalls:0`, `plnWrites:0` | В GitHub ЕСТЬ свидетельство INSTALLED smoke, более новое, чем аудит 17Z; это не наша независимая проверка реального локального окружения и не LIVE Archicad. |
| 06 | PR165 полнота выборки | `apa_high_density_readonly_v2.py:20` `SAMPLE_LIMIT=5000` | Таблицы samples ограничены; 5000 строк нельзя объявлять полной проверкой всех связей. |
| 07 | PR165 GUID | `apa_high_density_readonly_v2.py:112–133` `nativeGuidMappingChecked: False` | IFC GlobalId нельзя отождествлять с нативным Archicad GUID; остаётся открытая задача сопоставления. |
| 08 | ezdxf v1.4.5 MINSERT | `mozman/ezdxf@v1.4.5:src/ezdxf/entities/insert.py:663–698`, blob `a5c3d621793da3dcd7b292ff6438b94d2c14f005`: `mcount`, `multi_insert()` | Готовое перечисление виртуальных INSERT каждого узла массива; не создавать собственный геометрический генератор. |
| 09 | ezdxf `virtual_entities()` и MINSERT | Тот же файл, строки 603–650: метод выдаёт содержимое лишь первого INSERT массива | Вызов только `virtual_entities()` теряет остальные повторения; №2 проверить coverage, не считать это уже закрытым PR165. |
| 10 | ezdxf XCLIP | `insert.py:636–638`: `virtual_entities` не применяет clipping polygon XCLIP | Нельзя выдавать видимые контуры DXF за точную физическую геометрию без отдельного XCLIP QA. |
| 11 | ezdxf неоднородный масштаб | `insert.py:625–628` и документация `/blocks/insert.html`: TEXT/MTEXT/ATTRIB могут трансформироваться неверно | Данные текста и измерительные анкеры не доверять без отдельной проверки. |
| 12 | ezdxf OCS→WCS | `/blocks/insert.html`: `dxf.insert` — OCS, `matrix44()` — преобразование содержимого в WCS; `insert.py:680+` сетка смещается в OCS | Нужна явная система координат, нельзя складывать insert как WCS без преобразования. |
| 13 | ezdxf единицы блоков | `https://ezdxf.readthedocs.io/en/stable/concepts/units.html`: `$INSUNITS`, `block.units`, `conversion_factor`; автоматической конверсии блоков нет | Численные координаты без единиц нельзя превращать в метры APA. |
| 14 | ezdxf XREF | `https://ezdxf.readthedocs.io/en/stable/xref.html`: `xref.dxf_info()`, `attach/embed`, для DWG требуется внешний reader | Отсутствие подгруженного XREF нельзя интерпретировать как пустой блок; готовое чтение DWG не подтверждено. |
| 15 | SAF SDK точная версия | NuGet `StructuralAnalysisFormat 1.7.3`, выпуск 2025-04-04, Apache-2.0, `.NETStandard2.0`: `https://www.nuget.org/packages/StructuralAnalysisFormat/1.7.3` | Готовый SAF Excel SDK, не FEM solver и не доказанный runtime в APA. |

## Первоисточники
- ezdxf исходник: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py
- ezdxf docs: https://ezdxf.readthedocs.io/en/stable/blocks/insert.html ; https://ezdxf.readthedocs.io/en/stable/concepts/units.html ; https://ezdxf.readthedocs.io/en/stable/xref.html
- APA PR165: https://github.com/dvikt33-ux/safe-bim-layer/pull/165
- APA PR164: https://github.com/dvikt33-ux/safe-bim-layer/pull/164
- NuGet SAF: https://www.nuget.org/packages/StructuralAnalysisFormat/1.7.3

**Гейты для этих 15 проверок:** SOURCE=VERIFIED_SELECTED; OFFLINE=NOT_RUN_THIS_CYCLE; BUILD=NOT_RUN; INSTALLED=SELF_REPORTED_PR165_ONLY; LIVE=NOT_RUN; ACCEPTED=NO.
