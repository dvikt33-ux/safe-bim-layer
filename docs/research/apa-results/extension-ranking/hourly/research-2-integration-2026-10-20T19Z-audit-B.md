# APA №2 · 19Z · Контрааудит B — интеграция и безопасность

Независимо сверены PR74/126/131/149/162/175/97 и требования BUILD-01 #192.

1. PR74 остаётся единственным compiler/SceneWriter/SQLite. PR126/162 — только стратегии, второй writer и повтор CloneNativeGroupV1 не нужны.
2. PR149 material-only Slab verifier допускает floorIndex=0, PR74 двухэтапный Slab включает thickness и оба этажа. Не подменять PR74 verifier без отдельного контракта.
3. PR131 требует проверенный host Wall GUID/story/library и отсутствие перекрытия проёмов.
4. PR175 snapshot проверяет байты и SHA, но не блокирует внешний Archicad writer. Reopen helper специализирован под Hotlink; общий BUILD-01 receipt пока NOT_FOUND.
5. PR97 GetModelDumpV1 читает только доступные тела регенерированного 3D-вида. Фильтры слоёв/design options/3D остаются, поэтому требуется census ожидаемых GUID и зафиксированный view state после реального Close/Reopen.

**Вывод:** SOURCE_ONLY; G4 BLOCKED до installed BREP provider и независимой проверки полноты. Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
