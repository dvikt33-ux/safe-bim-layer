# APA №1 BUILD-01 SOURCE 15–16
15. G2: В Tapir 1.5.9 CreateWalls floorIndex меняет смысл zCoordinate: смещение относительно этажа вместо абсолютной отметки. №2: явно различать оба вида высоты.
16. G2: В Tapir 1.5.9 CreateColumns isWidthAndHeightLinked по умолчанию true; для прямоугольного сечения разных размеров нужен false. №2: проверить ширину и глубину по результату.
Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp
Версия 1.5.9, MIT. Локальная 1.5.10 не проверена. SOURCE_ONLY, новых PASS нет. MODEL_MODE_NOT_VERIFIABLE.
