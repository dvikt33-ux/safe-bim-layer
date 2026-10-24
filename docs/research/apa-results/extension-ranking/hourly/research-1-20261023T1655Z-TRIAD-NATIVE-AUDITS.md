# APA №1 — два независимых контрааудита, 23.10.2026 16:55Z

## A1 — Контрааудит версий, лицензий и реального контракта [SOURCE]
**Сверенные источники:** https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://help.graphisoft.com/AC/27/INT/GC.pdf ; https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564.

| Проверяемое утверждение | Контраргумент | Решение |
|---|---|---|
| AC29/Rhino8 совместимы | Официальный build3000 от 01.10.2025 указан, но локальная GH component palette и версия плагина не читались | SOURCE_PASS; INSTALLED_UNKNOWN |
| Shell Ext/Rev/Ruled можно использовать | AC29 руководство индексирует все три метода, но нет локального GUID/BREP readback | SOURCE_PASS, LIVE_NOT_RUN |
| Custom CW можно задать через GH линии | Точные Custom Frame Axes/Panel Points показаны в официальном AC27 guide; AC29 подтверждает Scheme Settings/Custom distinction, но не выполнена локальная проверка всех входов | PARTIAL_SOURCE, требовать AC29 component inventory |
| Slab с holes через planar Surface | Документировано в официальном AC27 guide, но в PR74 текущий building сценарий явно отвергает сложные holes | HISTORICAL_SOURCE; BUILD-01 scope не расширять без теста |
| AC29 Opening можно автоматически создать из GH | Archicad имеет собственный Opening Tool; это не доказательство GH компонента | GH_NATIVE_OPENING_NOT_FOUND |
| Custom Window/Door не требует написания GDL | Save Selection as документирован для AC29, но это редактирование Embedded Library и непараметрический объект | SOURCE_PASS; не выполнять без разрешения |
| Бесплатность | Graphisoft add-on распространяется бесплатно, Rhino и Archicad требуют собственных лицензий; лицензии пользователя не проверялись | ADDON_FREE; RUNTIME_ENTITLEMENT_UNKNOWN |

**Дополнительное ограничение:** индексированный PDF AC29 имеет исторический титул/номер версии руководства; это не означает, что исполняемый модуль build3000 соответствует всем историческим иллюстрациям. Попытка прочитать PDF целиком через веб не удалась из-за размера, через shell URL не разрешился. Поэтому нет постраничного полного аудита AC29 guide; подтверждённые фрагменты не выдавать за весь документ.

**Контрааудит A1:** новых подтверждённых фактов INSTALL/LIVE нет; два узла (Custom CW exact inputs, Slab holes) требуют локального подтверждения именно AC29, хотя официальный исторический контракт существует.

## A2 — Контрааудит инженерной пригодности и защиты BUILD-01 [SOURCE + PR74]
**Прочитаны:** issue https://github.com/dvikt33-ux/safe-bim-layer/issues/192 и изменённый файл docs/APA_MODEL_FIRST_BUILDING.md PR https://github.com/dvikt33-ux/safe-bim-layer/pull/74. PR74 — уже действующий нативный контур и исторический 21-элементный результат, а не доказательство работы GH.

| Риск | Контроль до разрешённой записи | Fail-closed результат |
|---|---|---|
| Два native writer | Для каждого element step/GUID только один owner: SceneWriter для APA-owned, GH для GH-owned | Если один и тот же элемент принадлежит обоим — BLOCKED |
| GH пересоздал элемент | Native GUID до/после + SEO + host + библиотечная идентичность | Изменение GUID/потеря host или SEO — FAIL |
| CW распался на subelements | Проверить parent GUID, child count, frame/panel class/material, BREP | Неожиданные frame/panel изменения — FAIL |
| Slab hole стал только визуальной дырой | Native Slab inner contours, BREP, net/gross area; Opening GUID отдельно | Не считать native Opening, если есть лишь контур плиты |
| Одно окно породило несколько | 1 authored opening → 1 native Window/Door → 1 host Wall GUID | Дубликаты или неоднозначный host — FAIL |
| Сложная форма стала Morph/GDL | Native type строго Shell/CW/Slab/Window/Door по задаче | Morph/GDL не эквивалент требуемому BIM-типу |
| Смена исходной GH геометрии | Граница commit: GH solver/Sync off до проверки; затем только отдельная санкционированная запись | Нельзя заявлять транзакционность от одного Boolean Toggle |
| Save/Open | После реального reopen сравнить GUID, type, story, material, host, SEO, BREP и отсутствие duplicates | Без независимого reopen — NOT_ACCEPTED |
| Соответствие СП | Отдельные проверки нормативных параметров и инженерное заключение | Native BIM сам по себе не доказывает СП |

**Критическое разграничение:** GH может создавать Shell/CW/Slab, но это НЕ означает универсальную двустороннюю синхронизацию AC↔GH↔Rhino и не означает автоматическое обновление APA BIM Graph/SQLite. Готового механизма согласования двух независимых write owners с AC GUID без дополнительной разработки в изученных источниках не найдено.

**Решение A2:** P0 остаётся G0 read-only inventory + G1 компилятор PR74 + G2 точные native contracts. GH Shell/CW/Slab — отдельный SOURCE-список для будущего расширения, не препятствие первому 21+ element BUILD-01. Приоритет №2: подготовить таблицу маршрутов и доказательств без установки, кода или LIVE.

## Проверка внутренних отчётов
- Точно прочитаны NEXT_RESEARCH_PRIORITIES.md (blob 6f074693360231c5cb42ada815984a6b0dd504c0), TRIAD-PIVOT (blob 896fa3af0953468ca58fca710f32cb926504f582), №1 15:59Z index и карточки №1 13Z/13:56Z/14:57Z/15:59Z, issue192 и PR74 changed-file patch.
- Свежие отчёты №2/№3 и исходная матрица 61: достоверные пути в текущем проходе не найдены, содержимое не прочитано; НЕ заявлять их аудит.
- PROJECT_PLAN rev182: упоминается в очереди, но исходный файл напрямую не прочитан; никаких изменений.
- Публикация только исследовательская, main/PLN/APX/код не затронуты.

**Ворота:** G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4 NOT_RUN, G5 NOT_RUN. Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED = 0.

MODEL_MODE_NOT_VERIFIABLE.
