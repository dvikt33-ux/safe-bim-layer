# APA AC29 — аудит 16Z, проверки 11–20

11 VERIFIED_UI: AC29 Multiply — GUI Drag/Rotate/Elevate/Matrix; программный API не доказан.
12 VERIFIED: SDK29 API_EditPars blob fb02dfa1 содержит typeID, withDelete, origC, begC, endC; matrix count отсутствует.
13 VERIFIED: SDK29 Grouping blob 96995b50: CreateGroup с массивом GUID и parent.
14 VERIFIED: Tapir CreateGroups blob 0231e8cc возвращает per-item errors при общем NoError.
15 VERIFIED: Tapir Hotlink blob 99053b4c требует hotlinkNodeId, origin; rotationAngle в радианах.
16 VERIFIED: SDK29 Hotlink blob 277e3122: GetHotlinkInstances по node GUID.
17 HIGH_RISK: Tapir Publisher blob 5899ab5a с пустой выборкой публикует весь набор.
18 VERIFIED: Graphisoft SDK LICENSE v2, Tapir MIT; local 1.5.10 не равна upstream.
19 VERIFIED: SDK29 MEP Place blob 27d7cd3a принимает карты сечений сегментов.
20 GAP: Tapir1.7.1 MEP blob a59e0b17 передаёт пустые карты. A11.S10 BLOCKED.

Поручения: №1 найти готовый API29 Multiply и MEP wrapper; №2 проверить local Tapir, per-item errors, Hotlink node/instance и Publisher whitelist. Контрааудит A: SOURCE не равен ABI/local LIVE.