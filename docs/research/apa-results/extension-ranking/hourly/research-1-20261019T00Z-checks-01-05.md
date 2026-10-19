# APA №1 — проверки 01–05, 19.10.2026 00Z

Источник: официальный Graphisoft DevKit29 tag 29.3100, файл docs/class_a_c_a_p_i_1_1_design_options_1_1_design_option_manager.html, blob feab8e4c2ebb2dc94f571cc67946119519d40cb9.

01. **Инвентаризация вариантов**: GetAllDesignOptions(), L162, возвращает vector<DesignOption>. SOURCE: варианты без PLN-копий. Контрааудит: это не CloneNativeGroupV1. №2: GUID и права.
02. **Состав варианта**: GetElementsOfDesignOption(option), L164, возвращает vector<API_Guid>. SOURCE: связь элементов и варианта. Контрааудит: не доказывает совпадение геометрии. №2: сопоставить GUID BIM Graph.
03. **Вариант вида**: GetDesignOptionCombinationSettingsOf(view), L152. SOURCE: проверка до Publisher. Контрааудит: не PDF readback. №2: статусы MainModelOnly/Standard/Missing.
04. **Hotlink instance**: GetHotlinkInstanceDesignOptionTable(API_HotlinkType), L168. SOURCE: варианты конкретного экземпляра. Контрааудит: PR173 Hotlink batch не тестировал Design Options. №2: read-only fixture.
05. **Hotlink node**: GetHotlinkDesignOptionTable(API_HotlinkNode), L166. SOURCE: варианты исходного узла. Контрааудит: node != instance. №2: сверить node/instance mapping.

Лицензия Graphisoft DevKit29 EULA, Windows 11/AC29 SDK source confirmed, локальный Tapir 1.5.10/ABI NOT_VERIFIED. Никаких новых BUILD/INSTALLED/LIVE/ACCEPTED.
