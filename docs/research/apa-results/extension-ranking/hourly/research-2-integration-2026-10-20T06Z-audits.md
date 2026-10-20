# APA №2 — восстановленное приложение 06Z: audits

Источник: локальный неизменённый журнал `APA_Research2_Integration_2026-10-20T06Z_CHECKS.md` (17 307 байт). Ниже воспроизведён соответствующий раздел без исправления исторических выводов. **LOCAL_ONLY; GitHub-публикация не подтверждена.**


**А — API/ABI/лицензии:** пересмотрены точные исходники Tapir tag1.5.9 (MIT), ezdxf v1.4.5 (MIT), IfcOpenShell0.8.5 (LGPL), Graphisoft SDK29.3000/3100 (EULA). Обнаружены исправления 4009/BADDATABASE в tagged SOURCE; нельзя переносить их на непроверенный локальный APX1.5.10. IfcDiff0.8.5 отличается default от новых online docs. Ни один установленный wheel, binary SHA, ABI build5101 не проверен. **Результат: SOURCE_ONLY.**

**Б — граф/дублирование/безопасность:** PR131 уже даёт host-fit; PR189 — DXF preflight; PR190 — group-intent; PR191 — узкий Slab copy. Запретить второй Router/SceneWriter/IFC parser. Publisher empty=whole-set risk, child-error ≠ leaf, XCLIP inverted не доказан, IFC all-peer должен сохранять GUID связей, IfcDiff пропускает FeatureElement. **Результат: адаптеры минимальные, все новые LIVE запрещены до разрешения.**
