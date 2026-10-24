# APA №1 02Z · SOURCE 10–12

SDK29 tag 29.3100, Graphisoft EULA. Runtime AC29 build5101/Tapir1.5.10 NOT_VERIFIED; no LIVE.

**10. Есть ли штатная проверка значения?** [IsValidValue](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___property.html#L371), blob `fa24d8f87c8a`. Свидетельство: API_PropertyValue+Definition → bool. Вывод: готовый read-only контракт. Контрааудит: Не норматив СП. Далее: Navigator.

**11. Как найти Publisher Set без публикации?** [GetNavigatorSet](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___navigator.html#L417), blob `aae2d47d51cb`. Свидетельство: API_NavigatorSet+index → Navigator Map/Publisher Set. Вывод: готовый read-only контракт. Контрааудит: Наличие ≠ опубликованный PDF. Далее: Настройки вида.

**12. Как проверить сохранённый вид?** [GetNavigatorView](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___navigator.html#L432), blob `aae2d47d51cb`. Свидетельство: API_NavigatorItem → API_NavigatorView. Вывод: готовый read-only контракт. Контрааудит: Не доказательство графической корректности. Далее: IFC классификация.

