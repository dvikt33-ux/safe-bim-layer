# APA №2 04Z — независимый контрааудит А: первоисточники

Сверены: `alesdev88/Archicad-MCP` tag v0.8.0 commit 74d4ecc67581e60b552b6ef7f6ac47d187e0f2a6; pyproject.toml (MIT, Python>=3.12, fastmcp>=3,<4, multiconn_archicad>=0.6,<0.7), LICENSE; Tapir tag 1.5.9 PropertyCommands.cpp; Graphisoft GDL HSF docs и AC29 Python API.

GetPropertyValuesOfAttributes — подтверждённый tagged Tapir метод, но локальная сборка 1.5.10 и ABI не проверены. GetPropertyValuesOfElements в Tapir и официальном JSON имеют одинаковое имя, но разный исходный код; отсутствие ComposeResult в Tapir не доказывает безопасность native property evaluation. GetAllProperties читает definitions, не значения. Значения атрибутов Tapir преобразует в строки, typed units отдельно не гарантированы.

MIT внешнего кода не распространяется на лицензию Archicad, LP_XMLConverter и импортируемые OBJ/3DS ассеты. Команда hsf2libpart подтверждена Graphisoft, но локальный converter binary SHA неизвестен. Эвристика OBJ масштаба (>100→мм; >5→см; иначе м) опасна для зданий. XML byte-exact roundtrip не гарантирует сохранение 3D Axonometry при импорте в AC29.

Итог А: SOURCE подтверждён по файлам, INSTALLED/LIVE для новых функций NOT_VERIFIED, лицензии цепочки требуют отдельной сверки.
