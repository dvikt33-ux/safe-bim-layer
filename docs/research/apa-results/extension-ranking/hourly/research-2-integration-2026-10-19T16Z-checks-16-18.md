# APA №2 16Z — технические SOURCE проверки 16-18

16. Вопрос: rich CreateRules batch atomic? Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicOverrideCommands.cpp#L424-L485 . Факт: per-item error and continue; groups may be created. Вердикт ADAPTER partial-success gate; fixture 2 good+1 bad.
17. Вопрос: legacy CreateGraphicalOverrideRule безопасен? Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicalOverrideCommands.cpp#L135-L193 . Факт: same-name rule overwritten. Вердикт REJECT automatic legacy write; duplicate name fixture.
18. Вопрос: GetViewSettings combo GUID? Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/NavigatorCommands.cpp#L316-L401 . Факт: combination is name, not GUID. Вердикт ADAPTER unique name→GUID join, ambiguous=reject.

Статус: SOURCE, новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED = 0.
