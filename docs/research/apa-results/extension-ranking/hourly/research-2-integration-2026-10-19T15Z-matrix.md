# APA №2 — 15Z — матрица 10 путей подключения
Оценки — экспертная польза 0–100, не ускорение. Контракты pinned Tapir 1.7.2, Graphisoft AC29, ezdxf 1.4.5. Ссылки на исходники в checks A/B/C.

| №/польза | APA → существующий интерфейс → готовый инструмент → результат | Выбор/трудность/риск | Критерий ГОТОВО |
|---|---|---|---|
| 1/100 | Router→Tapir GetViewSettings→BIM Graph: navigator GUID[]→settings/error[] | REUSE БЫСТРО; custom name | capability true, N=N, errors=0 |
| 2/99 | Router→Tapir 1.7.2 GetGraphicOverrideRules→Graph: GUID/XML/style/group | ADAPTER АДАПТАЦИЯ; silent skip/version | count, style, missing NOT_PROVEN |
| 3/100 | Router→Tapir structured criterion→guard: 666 keys→XML | ADAPTER АДАПТАЦИЯ; CRITICAL multi-key | exactly-one OFFLINE fixtures, scope not all |
| 4/98 | Router→Tapir CreateGraphicOverrideRules: batch→GUID/error[] | DEFER АДАПТАЦИЯ; partial/orphan group | 2 good+1 bad, ordered errors, no orphan |
| 5/97 | Router→Tapir CreateGraphicOverrideCombinations: ordered GUIDs | DEFER АДАПТАЦИЯ; priority/order | exact rule order readback |
| 6/99 | Router→Tapir legacy CreateGraphicalOverrideRule/Combination | REJECT automatic; name-upsert overwrites | GUID/name/group preflight denylist |
| 7/100 | Router→existing GuardedSaveTransport→native Save | REUSE БЫСТРО; direct SaveProject(path) overwrite | scratch identity/SHA/save/reopen |
| 8/99 | Router→Tapir DeleteElements→BIM Graph inventory | REUSE БЫСТРО; nonexistent GUID success | before-present/after-absent |
| 9/96 | Router→existing C1→ezdxf 1.4.5 recursive_decompose | ADAPTER АДАПТАЦИЯ; XCLIP ignored | 2×3 cell provenance, XCLIP_UNKNOWN |
| 10/95 | Router→Tapir 1.7.2 Grid/LevelDim→BIM Graph | DEFER АДАПТАЦИЯ; GDL/units/sentinel | warnings=0, parent hit, no -110000000 |

MEP read-only: GetMEPPreferenceTables (Piping/Ventilation; angle/transition AC29), GetMEPSystemGroups AC29 → существующий V2; DEFER local capability/MEP license, AC30-only ElectricalPanels excluded.

Выбор A: Router→Graphisoft JSON AC29 ExecuteAddOnCommand→existing Tapir→BIM Graph. Альтернатива B: собственный SDK29 APX отклонена (ABI, сопровождение, второй исполнитель). Готовый APX 1.7.2 AC29 Win существует, но локальная 1.5.10 не сравнена, устанавливать нельзя. Tapir MIT; SDK29 отдельная лицензия Graphisoft.

Gates: SOURCE→OFFLINE negative fixtures→BUILD Windows Python 3.11/3.12→INSTALLED с backup/SHA/разрешением→LIVE scratch PLN GuardedSaveTransport→ACCEPTED независимый GUID/style/geometry readback. Сейчас SOURCE ONLY. 8GB VRAM не требуется для JSON read-only; 48GB RAM не гарантирует обработку произвольного объёма DXF.
