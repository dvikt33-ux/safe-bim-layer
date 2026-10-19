# APA AC29 — №2, 19.10.2026 06Z
27 SOURCE-проверок (P01–P27) и два контрааудита. Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED не проводились. MODEL_MODE_NOT_VERIFIABLE.

Прочитано: NEXT_RESEARCH_PRIORITIES.md blob 2cb49edc (последний аудит №3 18.10 20Z), priority_matrix_20261018.json blob 9cb5e6f2 (61 кандидат), candidates.json, №1 06Z blob 7641b990 (7 карточек d80b6462), №2 05Z blob 12f4380e; канон control/PROJECT_PLAN.json revision182 blob c2ab2f9d (только чтение). PR165 V2, PR168 C1, PR170 B3, PR160, PR173, PR175. Исходники IfcOpenShell tag ifcopenshell-python-0.8.5.

## Матрица
| Кандидат | APA → готовый адаптер/интерфейс → результат | Вердикт | Польза* | Сложность | ГОТОВО (будущий gate) |
|---|---|---|---:|---|---|
| IFC host triple | Router → PR165 _ifc_openings → join Fills/Voids → BIM Graph | REUSE+ADAPTER | 97 | БЫСТРО | 3 GlobalId; orphan/duplicate не PASS |
| 3D mapped mirror | Router → PR170 B3 → util.placement/representation 0.8.5 → QA | ADAPTER | 96 | АДАПТАЦИЯ | determinant/Scale2/Scale3; 2D NOT_SUPPORTED |
| Геопривязка | Router → PR165 _ifc_georef → util.geolocation → QA | REUSE+ADAPTER | 95 | БЫСТРО | MapConversion+CRS; missing NOT_VERIFIED |
| IFC группы/типы | Router → V2 → util.element → bounded group graph | ADAPTER | 92 | АДАПТАЦИЯ | cycle-safe; IFC group != native |
| Материальные слои | Router → V2 → get_material_layers → QA | ADAPTER | 91 | БЫСТРО | NOT_LAYERED vs [] + units |
| Единицы QTO | Router → B2/V2 → util.unit → typed QA | REUSE+ADAPTER | 93 | БЫСТРО | UNKNOWN_UNITS, zero != missing |
| Face provenance | Router → B3 → util.shape → IFC item trace | ADAPTER | 90 | АДАПТАЦИЯ | nonmanifold NOT_VERIFIED; item ID != GUID |
| MEP owner/peer | Router → PR165 _ifc_ports → util.system → BIM Graph | REUSE+ADAPTER | 96 | БЫСТРО | orphan/peer/flow/reciprocity |
| MINSERT 2×3 | Router → PR168 C1 → ezdxf Insert.multi_insert → 6 cells | ADAPTER | 96 | АДАПТАЦИЯ | 6 row/col receipts, XCLIP UNKNOWN |

*Баллы — экспертная польза, НЕ измеренное ускорение. IfcOpenShell 0.8.5 LGPL-3.0+, ezdxf 1.4.5 MIT, Graphisoft Python 29.3000 Apache-2.0. Локальная сборка Tapir 1.5.10 не проверялась в этом цикле.

## Выбор и gates
Для host использовать существующий PR165 join, не новый парсер; для IFC world bounds — PR170 B3, не второй IfcConvert; для MEP — util.system, не SDK29 addon; для MINSERT — штатный multi_insert, не самописную матрицу. Прямой готовый 2D mapped wrapper для 0.8.5 NOT_FOUND в проверенном source; минимальный adapter: 2D NOT_SUPPORTED и explicit negative test. Программный запуск XCLIP C1 не подтверждён.

SOURCE=27 (приложения); OFFLINE=NOT_RUN (fixtures IFC4/IFC2X3/DXF, negative cases); BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED_FOR_NEW_ADAPTERS; LIVE=NOT_RUN; ACCEPTED=NO. Будущая проверка: SHA исходника и vendor wheel, new output only, readback SHA, bounded file/report, units+GUID+frame, fail-closed. GPU не требуется; 48 GB RAM не гарантирует 4 GiB IFC; PR165 ограничивает input 4 GiB/output 200 MiB/1200s. Откат — удаление только нового JSON sidecar.

№1: найти IFC host triple, 2D mapped wrapper, IFC2X3 ePSet CRS, cycle-safe group walker, non-layer material variants, manifold checker, MINSERT 2×3 с XCLIP/ATTRIB. №3: на OFFLINE утверждение host, MEP, MINSERT, mapped 3D, geo, QTO, bounded groups, material layers.

Проверки: research-2-integration-2026-10-19T06Z-checks-A/B/C.md; контрааудиты: research-2-integration-2026-10-19T06Z-audits.md. Никаких изменений main/PLN/APX/кода/PR/очереди №3/плана182.
