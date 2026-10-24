# APA №2 | 2026-10-24 07Z | Два документарных контрааудита (не независимый №3)

## Контрааудит A — «GH Beam закрывает CreateBeams PR74»

**Проверяемая гипотеза:** если официальный Graphisoft Live Connection AC29 имеет компонент Beam, можно считать Beam готовым внутри authored PR74/SceneWriter без нового кода.

**Фальсификация:** GC.pdf стр.26 действительно подтверждает native Beam и 3D Curve, в том числе Complex Profile; но pinned PR74 compile_authored_intent allowlist (lines 293–296) не содержит CreateBeams, а GH Beam записывает через другой официальный механизм, минуя SceneWriter/SQLite receipts. Совпадение native BIM-типа не доказывает совпадения owner, GUID, idempotency, transaction guard и Save/Open. 3D curve в GH может порождать несколько сегментов, что меняет кардинальность и GUID map.

**Вердикт:** GH-owned Beam SOURCE_SUPPORTED, APA-owned Beam через существующий authored PR74 **NOT_FOUND**. Путь GH Beam в общем BUILD-01 требует отдельного разрешения, изоляции владельцев, runtime check и нативного G4; не писать в APA-owned GUID. Не добавлять CreateBeams в allowlist и не создавать новый writer.

## Контрааудит B — «Synchronise=False и Cache Action=False образуют трёхсторонний стоп/снимок»

**Гипотеза:** достаточно выключить два Boolean, чтобы получить единый frozen state и остановить весь обмен AC↔GH↔Rhino.

**Фальсификация:** разработчик McNeel (Rhino8.1, 16.11.2023) говорит о **frozen output Rhino Query** до expire/Query; Graphisoft Design Synchronize=False (GC.pdf стр.17; №2 06Z) выдаёт **Null**, не frozen output. McNeel Content Cache Action=False (guide 17.05.2024) не выполняет action, но видимый Result продолжает Pull. Отдельный AC→GH Sync Changes to GH может обновлять references; отдельный APA SceneWriter вообще не управляется этими Boolean. Никакого durable snapshot, global lock, crosswalk GUID или атомарного rollback нет.

**Вердикт:** READ-only Query freeze не равен SAVE; скрыть Result для остановки Cache Pull, но не выдавать это за остановку других writers. Сохранить .3dm/.gh и hashes, сравнить AC PLN/port/GH document; STOP при UNKNOWN owner/feedback loop. Полная трёхсторонняя синхронизация **NOT_FOUND**.

**Ограничение аудитов:** только документарная проверка, не запуск на AC29 build5101/Rhino8 SR. Не независимый аудит №3. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.
