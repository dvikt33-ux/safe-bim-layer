# APA №1 — research-1-20261023T1723Z-TRIAD-OWNERSHIP — проверенный индекс

## Влияние на BUILD-01
**Новый P0 риск:** официальный AC29 GH–Archicad Live Connection при удалении GH Object Settings / переключении на existing Library Part удаляет созданную GH библиотечную деталь из Embedded Library, оставляя Missing Objects. Дополнительно AC29 официально подтверждает: только одна GH definition связана с Archicad одновременно; GH-controlled параметры перезаписывают ручные AC правки при reconnect; copy-paste отвязывает копии от GH; модальные окна приостанавливают соединение. Историческая документация Graphisoft описывает Teamwork duplicates/stale elements/SEO loss и false-Synchronize stale behavior — на AC29 НЕ подтверждено.

**Практический вывод:** до любого нового GH→AC WRITE нужен read-only preflight точной пары GH definition↔PLN, ownership по полям, library inventory, настоящий native GUID, число объектов и отсутствие Teamwork reservation conflicts. Для APA-owned элементов только существующий PR74/SceneWriter, GH — геометрия→jSwan→typed JSON. Никакой новой нативной записи и автоматического 3-way sync не доказано.

## BUILD-01 gates
G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4 NOT_RUN; G5 NOT_RUN. SOURCE=30 отдельных предметных утверждений; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. FULL_THREE_WAY_SYNC=NOT_FOUND.

## Приложения, create→fetch exact readback
- [research-1-20261023T1723Z-TRIAD-OWNERSHIP-SOURCE.md](research-1-20261023T1723Z-TRIAD-OWNERSHIP-SOURCE.md): commit `378ca5a5dc6260cd2e3fba4dc0364602c6ff1038`; blob `1b525fe65bc687027a0227dab571bd45d91483d4`; chars=7953; exact_readback=true
- [research-1-20261023T1723Z-TRIAD-OWNERSHIP-CARDS.md](research-1-20261023T1723Z-TRIAD-OWNERSHIP-CARDS.md): commit `55d366dc0d9d89e3d03e82d74b130a2c71d7a6cb`; blob `215641b0be46c727ae3a78b0489b6d6a1aa34cce`; chars=7348; exact_readback=true
- [research-1-20261023T1723Z-TRIAD-OWNERSHIP-AUDITS.md](research-1-20261023T1723Z-TRIAD-OWNERSHIP-AUDITS.md): commit `c6e10d1e6a2183235316dcbb5b4acf1fa8109ecb`; blob `60b59c8737f30b09dfdbe2269eb0f5dd5d2436b5`; chars=3897; exact_readback=true

## Контекст и независимые источники
Прочитаны NEXT_RESEARCH_PRIORITIES.md (blob 6f074693360231c5cb42ada815984a6b0dd504c0), TRIAD-PIVOT (blob 896fa3af0953468ca58fca710f32cb926504f582), №1 15:59Z и 16:55Z, свежий №2 17Z (index blob 49844455b2c2736c821d4f64182891339207403f), матрица 61 (blob 9cb5e6f2a59f80762cc77073eeb10404829af75a), №3 последний найденный 20.10 07Z (blob 40742adbf7ec945b31d125aac6912d95e5f07920), issue192, PR74, Graphisoft AC29 GC/GDL и исторические статьи Graphisoft Community. Более свежий №3 не найден/не заявляется прочитанным. Исторический PROJECT_PLAN rev182 только чтение через ссылки очереди; сам файл не извлечён.

## Поручение №2
Приоритет: C1723-01 (Library Part lifecycle) → C1723-02 (exact GH/PLN connection) → C1723-03 (per-parameter ownership) → C1723-04 (Teamwork conflicts) → C1723-05 (Sync false vs deletion) → C1723-06 (provenance/detached copies) → C1723-07 (native GUID readback). Ни установки, ни LIVE без отдельного допуска.

Ограничения: официальный AC29 PDF был доступен в поисковой индексации, но прямое скачивание 22.8 MB не удалось; полный постраничный аудит не выполнен. Исследовательский SOURCE не равен local pass. Не изменены main/код/PLN/APX/установки/PROJECT_PLAN/NEXT/merge. MODEL_MODE_NOT_VERIFIABLE.
