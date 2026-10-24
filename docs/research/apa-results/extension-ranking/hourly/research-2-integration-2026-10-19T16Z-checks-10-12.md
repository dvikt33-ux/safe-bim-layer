# APA №2 16Z — технические SOURCE проверки 10-12

10. Вопрос: Tapir SaveProject(path) безопасен? Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/ProjectCommands.cpp#L1363-L1411 . Факт: existing path overwritten; read-only refusal may be bypassed. Вердикт REUSE GuardedSaveTransport, path collision fixture.
11. Вопрос: DeleteElements success доказывает существование? Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/ElementCommands.cpp#L4766-L4805 . Факт: missing GUID returns success when absent afterwards. Вердикт ADAPTER before/after GUID inventory; negative missing GUID.
12. Вопрос: and+or в criterion? Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicOverrideCriterion.cpp#L1073-L1082 . Факт: hasOr=!hasAnd && Get(or). Вердикт ADAPTER exactly-one; reject simultaneous keys.

Статус: SOURCE, новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED = 0.
