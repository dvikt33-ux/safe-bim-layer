# APA №1 — сравнительная матрица 00Z, 19.10.2026

Экспертный балл = приоритет полезности, **не** измеренное ускорение. Время внедрения — качественная оценка; инженерный способ подключения исследует №2. Для всех строк SOURCE, OFFLINE/BUILD/INSTALLED/LIVE не проводились, ACCEPTED=NO.

| Готовая возможность | Балл | Лицензия | Windows 11/AC29 | Оценка усилий | Что закрывает | Риск |
|---|---:|---|---|---|---|---|
| Design Options Manager SDK29 | 95 | Graphisoft EULA | SDK29 29.3100; ABI NOT_VERIFIED | Средне | Варианты, GUID, виды, Hotlink mapping | Права Teamwork, не Clone |
| Native Structural Analytical API | 93 | Graphisoft EULA | SDK29 29.3100; ABI NOT_VERIFIED | Средне | Native SAM inventory/connectivity | SAF/solver/СП не подтверждены |
| buildingSMART IDS Audit Tool 1.0.124 | 93 | MIT | .NET8 CLI, Windows runtime NOT_VERIFIED | Низко-средне | Валидация самой IDS | NuGet artifact/версия не закреплены |
| MEP PhysicalSystem 29 | 91 | Graphisoft EULA | SDK29 29.3100; MEP entitlement NOT_VERIFIED | Средне | Persistent native system IDs | Logical ≠ physical; transition BLOCKED |
| IFC HookManager | 88 | Graphisoft EULA | SDK29 29.3100; ABI NOT_VERIFIED | Средне-высоко | IFC export-time metadata | Callback lifecycle, отсутствие готового Tapir route |
| Ifc2Sql 0.8.5 | 86 | LGPL-3.0-or-later | Python wheel NOT_VERIFIED | Низко-средне | IFC→SQLite QA snapshot | Disk writes, geometry BLOB, memory |
| IFC CRS QA 0.8.5 | 89 | LGPL-3.0-or-later | Python wheel NOT_VERIFIED | Низко | Detect missing CRS/unit shift | Silent fallback to unchanged XYZ |

**Аппаратная оценка:** CPU/RAM достаточность не измерялась; 48 GB RAM — ресурсный потолок будущих IFC/SQL; RTX4060 8 GB VRAM для этих SOURCE проверок не использовалась. Никакого заявленного ускорения.

**Ограничение:** AC29 SDK source подтверждён, но локальный Tapir 1.5.10 не тождествен upstream 1.5.9/1.7.1; Graphisoft SDK нельзя считать MIT. Canonical plan rev182 не изменялся.
