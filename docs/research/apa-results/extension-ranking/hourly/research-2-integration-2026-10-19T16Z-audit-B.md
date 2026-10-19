# APA №2 16Z — собственный контрааудит Б
Проверка дублирования: PR160 — PDF марки, PR162 — существующая стратегия SceneWriter, PR168 — DXF C1, PR170 — IFC B3, PR173 — LIVE-02 receipt, PR175 — draft SAFE-01. Не создавать новый Router, SceneWriter, IFC/DXF parser или CloneNativeGroup.
Альтернативы: rich Tapir через Graphisoft JSON AC29 лучше нового SDK29 APX; XClip metadata через C1 лучше второго DXF движка; validate(filepath) через B1/B3 лучше нового STEP parser; GuardedSave лучше прямого SaveProject(path).
Риски: PR173 receipt не binary ACCEPTED, PR175 cooperative lock не блокирует внешний Archicad; rev183 имеет активный lease. Вердикт SOURCE_CONDITIONAL. Нет benchmark ускорения.
