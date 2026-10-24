# APA №1 — SOURCE проверки 01–10 (23Z)

01. Канон rev182: PROJECT_PLAN.json blob c2ab2f9d; A11.S03 PARTIAL, S08/S10 BLOCKED, A07.S03 READY. Вывод: нельзя считать SAF/MEP завершёнными. Аудит: READY не DONE. №2: привязать решения к задачам.

02. Каталог 61 blob 87ee1c0b: IFCTESTER #4, IFCCLASH #8, BIMCOLLAB-BCF #29, отдельного IFCFM нет. Вывод: IfcFM — новый кандидат, остальное — углубление. Аудит: отсутствие ID не доказывает отсутствие кода. №2: проверить FM route.

03. PR154/159/160/162: изменены 5/6/5/7 файлов (GitHub list_pr_changed_filenames). PDF vectors, group acceptance, massops preflight, group-first selector уже существуют. Аудит: названия файлов не полноценный code audit. №2: duplicate scan.

04. Graphisoft AC29 C++ API group___markup.html L324–345: ACAPI_Markup_GetList(APINULLGuid,&markUps). Вывод: native read-only Issues inventory. Аудит: локальный APX не проверен. №2: SDK29 header.

05. Graphisoft API L222–245: ACAPI_Markup_ExportToBCF(fileLoc,markupEntryIds,useExternalId=false,alignBySurveyPoint=true). Вывод: native BCF export. Аудит: не Tapir JSON и не LIVE. №2: GUID/survey point.

06. Graphisoft API L347–375: ACAPI_Markup_ImportFromBCF(fileLoc,silentMode,callback,par1,...). Вывод: native BCF import. Аудит: мутирующая операция со встроенным undo scope. №2: read-only preflight.

07. Graphisoft API L416–441: ACAPI_Markup_ImportFromPDF, Since AC29, APIERR_BADNAME при не-Archicad PDF. Вывод: импорт замечаний, не PDF→BIM. Аудит: сторонние чертежи не поддержаны. №2: исходный формат.

08. AC29 help 082_IssueHandling-15.htm: UI BCF 3.0/2.1/2.0. Вывод: штатная поддержка BCF3. Аудит: UI не означает IfcClash BCF3. №2: roundtrip.

09. AC29 help 120_Interoperability-17.htm L4–13: Import IDS генерирует классификации и свойства. Вывод: готовый UI import. Аудит: не IFC QA. №2: read-only preview.

10. Та же справка L19–22: существующие свойства не меняются, выбирается IFC Property Mapping preset. Вывод: импорт дополняет, не синхронизирует значения. Аудит: нельзя объявлять автоматическое обновление. №2: schema diff.

Sources: https://graphisoft.github.io/archicad-api-devkit/group___markup.html ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-17.htm . SOURCE only; OFFLINE/BUILD/INSTALLED/LIVE NOT_RUN.
