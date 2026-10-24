# APA №1 — карточки C4–C6, 2026-10-19 01Z

SOURCE only; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=NO. Приоритет 0–100 — не benchmark.

## C4 SAM loads — 84/100
Функция: SDK29 tag 29.3100 ACAPI_Analytical_CreateAnalyticalLoadGroup/Case/Combination, API_AnalyticalLoadCombination::loadFactors.
Не дубликат: native SAM metadata, не IFC structural graph/solver; A11.S08 BLOCKED.
Что искать: готовый SDK29 analytical load read-only sample.
Лицензия/риски: Graphisoft EULA; Windows/AC29/Tapir1.5.10 local NOT_VERIFIED, СП loads и SAF artifact отсутствуют.
Вопрос №2: есть ли официальный пример чтения group/case/combination GUID и коэффициентов?
ГОТОВО: read-only load inventory, не повышение A11.S08 без SAF/solver.

## C5 IfcOpenShell validate — 94/100
Функция: IfcOpenShell tag ifcopenshell-python-0.8.5 validate.py:471–503, used_guids и IfcRoot.UR1; LGPL-3.0-or-later.
Не дубликат: готовая QA, не нужен второй checker; отличается от IDS IfcTester.
Что искать: готовый validate() + json_logger в существующей экосистеме.
Риски: Windows wheel/installed NOT_VERIFIED; IFC GlobalId != Archicad GUID; время не измерено.
Вопрос №2: можно ли получить JSON ошибки без нового движка и мутации IFC?
ГОТОВО: OFFLINE duplicate GlobalId→IfcRoot.UR1, unique→нет ошибки.

## C6 ifcbench — 57/100, условно
Функция: IfcOpenShell/ifcbench master, pyproject 0.0.1, Python>=3.10, metrics.py:151 hash_quantised_verts, bbox/volume/manifold/SQLite.
Не дубликат: сравнение IFC kernel/version tessellation, не Native Model Dump.
Что искать: только готовую официальную Windows-compatible версию с лицензией.
Риски: LICENSE_NOT_VERIFIED (GitHub license=null), runner.py:29 bin/python POSIX, Windows Scripts/python.exe; benchmark отсутствует.
Вопрос №2: есть ли готовый Windows релиз и явная лицензия? Иначе NOT_FOUND.
ГОТОВО: подтверждённая версия/лицензия либо обоснованное отклонение без установки.

Источники: https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___analytical.html#L657 ; https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/validate.py#L471 ; https://github.com/IfcOpenShell/ifcbench/blob/master/src/ifcbench/runner.py#L29 .
