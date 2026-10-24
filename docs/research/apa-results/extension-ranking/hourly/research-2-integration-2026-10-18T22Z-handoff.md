# APA №2 22Z — передача координатору №3 и ворота внедрения

Приоритеты №3 T2-20-01..08 проверены; актуальный №1 22Z прочитан. 61 кандидат из priority_matrix/candidates, PROJECT_PLAN.json revision182 (91 задач) — только чтение. Никаких новых ACCEPTED.

**Кандидаты для решения №3:** DXF XCLIP JSON 95; MEP IFC owner/peer 92; Publisher preflight 91; MINSERT per-cell 90; IFC PDF provenance 88; IFC mapped placement 86; 4D/5D read-only 76/79. Баллы — экспертная полезность.

**Ворота:** SOURCE: pinned source/version/license и APA reuse; OFFLINE: isolated DXF/IFC fixtures, source SHA, GUID/unit checks, negative cases; BUILD: pinned Python/SDK29 compile checks; INSTALLED: actual Windows environment/import/route receipt; LIVE: отдельное разрешение и scratch PLN, native journal; ACCEPTED: независимый повторный readback и инженерная приёмка. Пока в текущем цикле только SOURCE.

**Вопросы №1:** 1) Найти готовый source-handle mapping у ezdxf CustomJSONBackend после XCLIP; пока NOT_FOUND. 2) Есть ли штатный AC29 PublisherSet inventory по GUID в установленном Tapir 1.5.10? 3) Доказать экспорт IFC4 MEP ports/owners из AC29 5101. 4) Найти безопасный готовый IFC 4D offline viewer без CDN и новых движков. 5) Проверить per-cell MINSERT attrs/OCS/zero spacing и готовые fixtures.

**Поручение №3:** обновить очередь с учётом подтверждённого SDK29 Publisher и исторического LIVE-02 PR173; не повышать это исследование до LIVE. Не изменять main/PLN/APX/код/PROJECT_PLAN.
