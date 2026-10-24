# APA №2 01Z — проверки 10–12: GSM и IFC ports
SDK29 Graphisoft EULA; APA PR165 SOURCE. Источники:
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_g_s_m_object.html
https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py

10. Вопрос: идентификатор GSM? SDK29:177 `GetUnID(): Result<GS::UnID>`, main+revision. Tapir LibraryParts выдаёт только main. Нужен минимальный read-only adapter; далее лицензия.
11. Вопрос: квалификация GSM без записи? SDK29:183 `IsPasswordProtected`; 240–253 `GetLicense/GetLicenseVersion/GetParameters`; `IsPlaceable`. Metadata ≠ право распространения; protected scripts не читать. Далее IFC.
12. Вопрос: чего нет в APA MEP IFC? PR165:170–190 `_ifc_ports` считает `IfcDistributionPort`, `IfcRelConnectsPorts`, но возвращает только from/to GlobalId, без владельца. REUSE sidecar + util.system. Далее get_ports.
