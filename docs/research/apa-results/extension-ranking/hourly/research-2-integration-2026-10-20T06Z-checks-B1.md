# APA №2 — восстановление 06Z: SOURCE-проверки 16–22

**Происхождение:** неизменённый локальный файл `APA_Research2_2026-10-20T06Z-checks-B-RECOVERED.md`, раздел 16–22. Это **поздняя публикация реконструкции**, не первоначальная публикация 06Z; точная байтовая идентичность с утраченным исходным приложением не утверждается. Все выводы SOURCE, не LIVE/ACCEPTED.

16. **Возвращает ли Tapir ошибку чтения дочерних элементов?** [NavigatorCommands.cpp tag1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L1503-L1514): `ACAPI_Navigator_GetNavigatorChildrenItems(...)==NoError && !children.IsEmpty()`. Ошибка и ноль детей ведут к отсутствию поля `children`. **Вердикт:** ERROR ≠ LEAF; нужен error-aware census или `UNKNOWN_INCOMPLETE`. Далее — fixture partial tree.

17. **Какой официальный Publish ABI в SDK29?** [Graphisoft DevKit29.3100](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___project_operation.html), строки около 1075–1095: `ACAPI_ProjectOperation_Publish(const API_PublishPars*,const GS::Array<API_Guid>* selectedLinks=nullptr)`; `selectedLinks` optional publish-only-these. **Вердикт:** прямой SDK writer не нужен; дальше — whitelist GUID и sandbox output.

18. **MINSERT уже разворачивается?** [ezdxf v1.4.5 disassemble.py](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py#L542-L578), blob `5f3413710f05c81193a381a69d83538ecc5b86ab`: `recursive_decompose` вызывает `entity.multi_insert()` при `mcount>1`. **Вердикт:** REUSE, новый parser не нужен; далее — effective count и handle provenance.

19. **Применяет ли recursive_decompose XCLIP?** Тот же ezdxf, строки 563–570: явно не применяет; выдаёт объекты вне clip polygon. **Вердикт:** RAW ≠ VISIBLE; далее отдельная стадия 2D clipping.

20. **Есть ли готовое получение границы в мировых координатах?** [ezdxf v1.4.5 xclip.py](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xclip.py#L162-L180), blob `3c89d5d375a4b4acff988c156f01e8105b3b3139`: `XClip.get_wcs_clipping_path()` возвращает 2D WCS. **Вердикт:** REUSE без CAD engine; далее clip line/polyline/polygon.

21. **Можно ли безусловно доверять inverted XCLIP?** Тот же xclip.py, строки 45–65: комментарий автора о неясной структуре inverted polygons; эвристика `inner_polygon()` использует минимальную площадь bbox, outer bounds может быть догадкой. **Вердикт:** UNSUPPORTED при недоказанной границе, не выдавать её за видимую. Далее — fixture inverted с независимым CAD эталоном.

22. **Проверяет ли APA исходные DXF units?** [PR189](https://github.com/dvikt33-ux/safe-bim-layer/pull/189), `scripts/apa_dxf_source_preflight.py`: `$INSUNITS` допустимый code 1..24, `scaleCalibration='NOT_VERIFIED'`, `unitConversionApplied=False`. **Вердикт:** REUSE preflight, не считать units calibrated. Далее — сопоставление контрольного размера в метрах.

**Контроль:** проверки 23–30 находятся отдельно в `research-2-integration-2026-10-20T06Z-checks-B2.md`; остальные архивные файлы не переписаны.
