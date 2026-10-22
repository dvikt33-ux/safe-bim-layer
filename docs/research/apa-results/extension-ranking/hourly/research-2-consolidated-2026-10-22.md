# APA №2 — сводный отчёт BUILD-01, 21–22 октября 2026

Назначение: объединить выводы часовых исследований без изменения оригинальных отчётов. SOURCE-only; не является приёмкой здания. Issue: https://github.com/dvikt33-ux/safe-bim-layer/issues/192

## Основной результат
Существующие PR74/126/149/162 и Tapir содержат часть требуемых механизмов, но G0–G5 не закрыты на новой двухэтажной модели. SOURCE=исследовано; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. Исторический 21-элементный прототип не является новым BUILD-01.

## Девять маршрутов интеграции
| Gate | Приоритет | Барьер и минимальный маршрут | ГОТОВО |
|---|---:|---|---|
| G0 | 100 | Проверить SHA256 фактически загруженного APX, build, порт, registered commands/schema; provider version не равен installed contract. Runtime probe + IsAddOnCommandAvailable, без WRITE | подтверждён runtime contract |
| G1 | 100 | PR74 требует существующие этажи: разрешённая scratch PLN + bind_authorized_saved_copy + storyBindings | OFFLINE_PASS нового двухэтажного DAG |
| G2 | 99 | CreateSlabs PR149 не принимает structureType/buildingMaterialId; использовать существующий PR74 CreateSlabs→ModifySlabs→readback, после проверки схемы | материал и геометрия обоих этажей |
| G2 | 97 | Wall defaults/Complex Profile и координаты z колонн требуют проверки по GetStories/Favorites | точные геометрия и этаж |
| G2 | 98 | Door/Window требуют hostWall GUID, libraryPart/Favorite и readback ориентации | проверенные host и проёмы |
| G3 | 94 | PR126 packed create возвращает несколько GUID, PR74 created_guid ожидает один; нужен mapping batch receipt→DAG step в существующем SceneWriter/SQLite | детерминированные receipts |
| G3 | 90 | PR162 группирование только поддерживаемых типов; не дублировать CloneNativeGroupV1 | GUID и типы групп подтверждены |
| G3/G4 | 100 | GetAllElements({})/databases=[] не доказывает оба этажа; Navigator→DatabaseId→отдельный GetAllElements на этаж с проверкой ошибок | полный preflight/readback inventory |
| G4/G5 | 100 | GetModelDumpV1 отсутствует в pinned каталоге Tapir, регистрация APA APX неизвестна; 3D filters ограничивают BREP | Save/Close/Reopen + независимый BREP и второе новое здание |

## Контрааудиты
А: контракт и происхождение — точная версия, лицензия, бинарник APX, namespace TapirCommand, схемы и регистрация. Б: полнота и независимость — GUID обеих этажных баз, материалы, host, 3D-фильтры, защита от повторного CREATE при UNKNOWN.

## Архив и ограничения
В локальном рабочем контейнере найден 161 исходный файл исследований №2; составлен ZIP и SHA256-манифест. Эти двоичные вложения не загружены этим Markdown-коммитом. Предыдущие отчёты указывали 7/7 Git blob SHA для архива 06Z; checks-B реконструирован, не оригинал. Количество уникальных SOURCE-проверок за сутки не определено из-за повторов. Полный архив исследователей №1 и №3 отдельно не подтверждён. Не изменять NEXT, main, PROJECT_PLAN, PLN/APX или исходный код. MODEL_MODE_NOT_VERIFIABLE.

## Следующее действие
Закрыть G0 по фактически установленному APX; затем G1 OFFLINE на новом задании. Только после отдельного допуска выполнять G3–G5.