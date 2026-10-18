# APA AC29 — аудит 16Z, проверки 21–30

21 VERIFIED: SDK29 API_SavePars_Saf blob3025f11a содержит фильтр и имя транслятора, но не расчётный движок. A11.S08 BLOCKED.
22 HIGH_RISK: IfcPatch master CLI blob17825969 без -o использует output=input.
23 HIGH_RISK: IfcPatch write blob4fd9bf18 может переместить существующий файл при строковом output.
24 PARTIAL: ExtractElements master blob b2660a9d восстанавливает containment/aggregation, но host/port связи не гарантированы.
25 DEFER: SplitByBuildingStorey blob ac0db99d использует сырое имя этажа и прямой ContainedInStructure[0].
26 CRITICAL: APA draft ifc_diff blob7ac61d9e передаёт -r без attributes/geometry; IfcDiff v0.9.0 split() не добавляет их автоматически.
27 GAP: IfcDiff v0.9.0 blob343a1074 исключает IfcFeatureElement, включая проёмы, из обычного сравнения.
28 VERIFIED: IfcClash v0.9.0 blob7aa36380 требует mode и соответствующие tolerance/check_all или allow_touching/clearance.
29 RISK: IfcTester reporter v0.9.0 blob c4c79db3 создаёт BCF2; issue #7152 — имена viewpoint/snapshot.
30 GAP: ifcopenshell/simple_spf — внешний git submodule step-file-parser commit 9400d243; importability не доказана.

№1: готовые relation validators, BCF viewer, SPF wrapper. №2: отдельные профили IfcDiff, immutable IfcPatch, BCF ZIP reader. Контрааудит B: reuse IFC reader, без второго движка и без benchmark 100×.