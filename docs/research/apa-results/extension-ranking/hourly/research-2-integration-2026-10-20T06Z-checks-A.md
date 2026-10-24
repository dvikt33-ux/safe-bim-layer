# APA №2 — восстановленное приложение к 06Z

Текст раздела перенесён без изменения из исходного файла `APA_Research2_Integration_2026-10-20T06Z_CHECKS.md`, сохранённого 20.10.2026. Архивное восстановление 08Z; это SOURCE, не новый тест. Оригинальная публикация 06Z оставлена неизменной.

## Проверки 01–15: APA, PR131, Tapir

01. **Какой план сейчас канонический?** Источник: `dvikt33-ux/safe-bim-layer`, ветка `research/apa-verified-results-hub-20261010`, `docs/research/apa-results/control/PROJECT_PLAN.json`, blob `b079bb94ce94738ce6042ad99e1f45b588131447`. Параметр `revision=197`; это не историческая ревизия 182. **Вердикт:** только чтение; следующая проверка — зависимость выбранных задач от канона.

02. **Сколько решений в матрице?** Источники: `priority_matrix_20261018.json`, blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`, `count=61`, `priority_formula=12*need+7*(5-effort)+confidence`; `candidates.json`, blob `87ee1c0b66233bf713e273b8b7cd00eff3a422f9`, `total=61`. **Вердикт:** ранжирование не является benchmark; следующая проверка — фактический контракт для каждого приоритетного ID.

03. **Что поручил координатор №3?** Источник: `audit-2026-10-20-02-tasks-2.md`, blob `be23814d873403b51821d27bc8d6ea29f6bee5dd`, I02-01..08. Требования: Slab, PDF hosted, XCLIP, Publisher, group, receipts, Hotlink, IFC. **Вердикт:** восемь предметных направлений; следующая проверка — сопоставление с существующим Router.

04. **Есть ли свежая публикация №1?** Источник: `research-1-20261019T18Z.md`, blob `3614b672c536fb37864ef83c1aa2f1fe183d48bd`, H01–H10. По ожидаемому имени `research-1-2026-10-20T05Z.md` GitHub вернул 404; это не доказывает отсутствие файла с другим названием. **Вердикт:** использовать последний подтверждённый отчёт; следующая проверка — новые карточки №1 при их появлении.

05. **Существуют ли уже испытания по поручению №3?** Источник: `audit-2026-10-20-02.md`, blob `a1d972fda4750b7695ba705ca2f9eacca3d0c831`: 30 SOURCE, новых LIVE=0. **Вердикт:** повторный запуск запрещён; следующая проверка — опубликованные receipts по конкретным PR, а не общий статус.

06. **Есть ли готовый валидатор hosted-проёмов?** Источник: [PR131](https://github.com/dvikt33-ux/safe-bim-layer/pull/131), patch `scripts/archicad_strategy_discovery.py`, функция `_v2_host_batch`: `target['hostContext']`, `target['nativeCreateData']`, `host['guid']`. **Вердикт:** REUSE готовой host-валидации, а не NOT_FOUND для всего маршрута; недостающее звено — PDF mark→Wall GUID. Далее — fixture двух похожих стен.

07. **Есть ли контроль коллизий двух новых проёмов?** Тот же PR131 `_v2_host_batch`: интервалы `[centerOffset-width/2, centerOffset+width/2]`, условие пересечения `<=1e-7`. **Вердикт:** REUSE, допуск в модельных единицах; далее — fixture на соприкасающиеся и перекрывающиеся проёмы.

08. **Есть ли точная привязка проёма к этажу?** PR131 `_v2_create_row`: `expected.z=storyElevation+wall.zCoordinate+sillHeight`, x/y интерполируются по `begCoordinate/endCoordinate` стены и `centerOffset`. **Вердикт:** REUSE; PDF имеет координаты pt сверху вниз, поэтому без калибровки m и поворота листа нельзя выбирать host. Далее — трансформация и тест этажей.

09. **Учитываются ли уже существующие проёмы?** PR131 `_v2_create_row`: `existingOpenings` с `start/end`, проверка пересечений; вызов `archicad_bim_graph._hosted_fit_errors` с `CreateWalls` parent и `CreateWindows/Doors` child. **Вердикт:** REUSE готового проверки геометрии; PDF selector остаётся NOT_FOUND. Далее — отрицательный случай ambiguous host.

10. **Каковы обязательные поля Tapir CreateWindows?** [tag1.5.9 ExtendedElementCommands.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp#L3879-L3894), blob `bd5cd197e9ad2c0db9e40c1baff877bbdcbfae30`: `ownerWallId` и `centerOffset>=0`; `width/height>0`, `sillHeight` и Favorite — опции. **Вердикт:** штатный writer, второй не нужен; далее — marker/favorite qualification.

11. **Исправлена ли ошибка активной базы 3D для окон и дверей?** Тот же tagged C++, строки 294–318, 3925–3948 и 4095–4118: `SwitchCurrentDatabaseToFloorPlan`, `GS::OnExit` для возврата предыдущей базы. Upstream [PR559](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/559) merged 16.08.2026. **Вердикт:** SOURCE_FIXED в 1.5.9, не подтверждён локальный APX; далее OFFLINE/разрешённый LIVE на 3D/плане/другом этаже.

12. **Остаётся ли ошибка 4009 на пути ошибок Tapir?** [CommandBase.cpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/CommandBase.cpp#L52-L62), blob `c39e4f341f183a7e5c8f65fc1142d77ddf2cd848`: `GetResponseSchema()` возвращает пустой optional; `GetRawResponseSchema()` документирует форму. Upstream [issue483](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/483), [PR544](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/544). **Вердикт:** SOURCE_FIXED; не переносить историческую регрессию на локальную 1.5.10 без проверки. Далее — негативный API fixture.

13. **Можно ли интерпретировать пустой IFC lookup как NOT_FOUND?** [Tapir1.5.9 IFCCommands.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp#L59-L90), blob `401de11745903a739dce43a999f7f4df610381c7`: `FindElementsByGlobalId` при `!IsOk()` не добавляет результат. **Вердикт:** пустой список может скрывать ошибку; нужен typed `UNKNOWN_ERROR`. Далее — fixture API failure vs genuine empty.

14. **Что означает `selectedNavigatorItemIds=[]`?** [Tapir1.5.9 NavigatorCommands.cpp](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L83-L103), blob `df359f7bdf94f9004617cf616c6d38cb98be08ae`: `selectedLinksPtr` остаётся `nullptr` и передаётся в `ACAPI_ProjectOperation_Publish`. **Вердикт:** CRITICAL deny missing/empty, не нулевая публикация. Далее — preflight 0/1/N без запуска Publish.

15. **Можно ли считать name→GUID Publisher полным реестром?** Тот же NavigatorCommands.cpp, строки 7–23 и 1567–1607: `GetPublisherSetNameGuidTable()` пропускает неуспешный `GetNavigatorSet`, `GetNavigatorItemTree` без `publisherSetName` берёт index 0. **Вердикт:** explicit set и учёт ошибок обязательны; далее — duplicate-name, multiple sets, partial read.
