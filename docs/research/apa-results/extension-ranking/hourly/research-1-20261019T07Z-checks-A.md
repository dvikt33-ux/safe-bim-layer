# APA №1 07Z — source checks 01–15

Источник всех проверок: официальный Graphisoft Archicad 29 Python JSON API `archicad.releases.ac29.b3000commands` и `b3000types`: https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html . Версия AC29 документирована, локальный build 5101 и регистрация в APA НЕ проверены; Windows 11, лицензия Archicad; Tapir для этих штатных методов не требуется. GPU не требуется для metadata, RAM benchmark отсутствует. Каждый пункт — отдельный конкретный контракт и его инженерное ограничение, а не список названий.

| № | Функция | Точное поле/сигнатура | Возможность/блокер | Балл | Вопрос №2 |
|---:|---|---|---|---:|---|
|01|`CreateLayout`|`layoutName,layoutParameters,masterNavigatorItemId,parentNavigatorItemId`|Нативный лист; без master/parent GUID нельзя гарантировать правильное место|95|№2: существующий readback нового NavigatorItemId?|
|02|`CreateLayoutSubset`|`subsetParameters,parentNavigatorItemId`|Создание поднабора; номера листов не подтверждены автоматически|93|№2: есть ли сверка IDs после операции?|
|03|`CreateViewMapFolder`|`folderParameters,parentNavigatorItemId?,previousNavigatorItemId?`|Готовое создание папки видов; не создаёт модельный вид|94|№2: preflight GUID родителя без записи?|
|04|`CloneProjectMapItemToViewMap`|`projectMapNavigatorItemId,parentNavigatorItemId`|Клонирование пункта в карту видов, не BIM-элементов|94|№2: доступна ли проверка source→view?|
|05|`GetNavigatorItemTree`|`NavigatorTreeId(type,name?)`|name позволяет адресовать Publisher set; наличие узлов ≠ успешная публикация|91|№2: дерево Publisher читается без записи?|
|06|`GetNavigatorItemsType`|`navigatorItemIds`|Возвращает тип или Error для каждого отсутствующего ID|89|№2: сохраняется ли per-ID ошибка?|
|07|`MoveNavigatorItem`|`navigatorItemIdToMove,parentNavigatorItemId,previousNavigatorItemId?`|Штатный перенос узла; изменяет структуру проекта|83|№2: доступен только capability gate без вызова?|
|08|`RenameNavigatorItem`|`navigatorItemId,newName?,newId?`|Независимые имя и ID; риск нарушить ревизионные ссылки|88|№2: предусмотрена проверка уникальности ID?|
|09|`DeleteNavigatorItems`|`navigatorItemIds → List[ExecutionResult]`|Удаление узлов; результаты поэлементные, атомарность не доказана|54|№2: оставить DISABLED до отдельного разрешения?|
|10|`GetAttributeFolderStructure`|`attributeType,path?`|Без path возвращает корень; вложенные пути требуют обхода|92|№2: полный read-only обход атрибутов существует?|
|11|`GetAttributeFolders`|`attributeFolderIds → List[AttributeFolderOrError]`|Ошибочный GUID не равен пустой папке|91|№2: раздельный error статус?|
|12|`GetAttributesByType`|`attributeType → List[AttributeIdWrapperItem]`|Все атрибуты типа, не только реально используемые|88|№2: есть ли отдельный USED/UNUSED источник?|
|13|`CreateAttributeFolders`|`attributeFolders: List[AttributeFolderCreationParameters]`|Полный путь создаёт также недостающие родительские папки|83|№2: проверка пути без записи?|
|14|`MoveAttributesAndFolders`|`attributeFolderIds,attributeIds,targetFolderId`|Массовый перенос папок/атрибутов; потенциально меняет проект|79|№2: точный список затронутых GUID?|
|15|`RenameAttributeFolders`|`attributeFolderParametersList → List[ExecutionResult]`|Частичные ошибки не должны давать общий PASS|81|№2: поэлементный readback?|

SOURCE=15 static; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.
