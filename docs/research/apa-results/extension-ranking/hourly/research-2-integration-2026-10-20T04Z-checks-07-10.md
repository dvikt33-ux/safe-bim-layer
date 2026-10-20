# APA №2 04Z — проверки 07–10

07. Tapir1.5.9 NavigatorCommands.cpp L1590: без publisherSetName выбирается первый набор (idx=0). DENY; далее exact name.
08. L1506: ошибка чтения children скрыта. UNKNOWN; далее независимый census.
09. L7–23: ошибки GetNavigatorSet пропускаются; name→GUID не доказывает уникальность. DENY duplicate.
10. L63–105: пустой selectedNavigatorItemIds → nullptr в Publish. STOP; далее deny-empty fixture.
