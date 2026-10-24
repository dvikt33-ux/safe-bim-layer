# APA AC29 — исследователь №1 / 19Z / 30 SOURCE-проверок

Каждый пункт: конкретный вопрос о незакрытой функции → версия и первичный код → факт → ограничение/контрааудит. Это 30 чтений контрактов, НЕ 30 локальных испытаний.

**01.** [R] IFC GlobalId→Archicad GUID: AddOnMain.cpp:841–844 registers GetElementsByIFCIds introduced 1.5.1. NOT_VERIFIED in local Tapir 1.5.10.
**02.** [T] IFCCommands.cpp:23–40 requires ifcIds: array[string]. Scalar is not the documented contract.
**03.** [T] IFCCommands.cpp:43–93 elementsByIFCIds contains list elements for each ID: mapping may be 0..N, not guaranteed bijective.
**04.** [T] IFCCommands.cpp:71–80 uses IFCAPI::GetObjectAccessor().FindElementsByGlobalId then GetAPIElementID for AC28+.
**05.** [R] AddOnMain.cpp:845–848 registers reverse GetIFCIdsOfElements, introduced 1.5.1; no new IFC mapper required.
**06.** [T] IFCCommands.cpp:109–123 requires elements ref #/Elements for reverse lookup; not ifcIds.
**07.** [T] IFCCommands.cpp:163–177 returns distinct ifcId and externalIFCId via GetGlobalId/GetExternalGlobalId; neither equals native GUID by assumption.
**08.** [T] IFCCommands.cpp:149–160 returns error for missing/not-found element; :178–188 has legacy ACAPI_Element_GetIFCIdentifier fallback.
**09.** [G] Graphisoft AC29 Merge regenerates GlobalId, retains original as External IFC ID; identity is not invariant under Merge.
**10.** [G] Graphisoft AC29 Open/Hotlink import translator uses external template; Merge uses host project translator.
**11.** [GX] Graphisoft AC29 export has six Conversion Presets and IFC2x3/IFC4/IFC4.3 MVD compatibility; name is insufficient provenance.
**12.** [TM/RM] GetIFCExportTranslators main version 1.6.0 returns only name and preview (IFCCommands.cpp:873–910); absent in upstream 1.5.9.
**13.** [R] Tapir 1.5.9 AddOnMain.cpp:1064+ ExportIssuesToBCF introduced 1.0.6; native exporter exists.
**14.** [I] IssueCommands.cpp:720–749 required exportPath/useExternalId/alignBySurveyPoint; issues optional. No file write performed.
**15.** [I] IssueCommands.cpp:770–777 empty issues triggers export of ALL issues. Risk requires explicit allowlist.
**16.** [I] IssueCommands.cpp:733–735 useExternalId chooses original external IFC ID vs Archicad IFC ID.
**17.** [I] IssueCommands.cpp:737–739 alignBySurveyPoint chooses Survey Point vs Project Origin.
**18.** [I] IssueCommands.cpp:783–790 invokes ACAPI_Markup_ExportToBCF; successful ExecutionResult is not proof of BCF2.1 schema.
**19.** [I] IssueCommands.cpp:832–851 ImportIssuesFromBCF calls ACAPI_CallUndoableCommand; MODEL WRITE, excluded.
**20.** [BV] release_2_1 bcf.version:3–5 declares VersionId=2.1, DetailedVersion=2.1; root README stale 2.0.
**21.** [B] BCF 2.1 Documentation:32–54 .bcf ZIP, bcf.version, UUID topic folder, markup.bcf, viewpoint.bcfv and snapshot PNG.
**22.** [BM] Schemas/markup.xsd:10–11 viewpoints maxOccurs=unbounded, :31–40 viewpoint/snapshot/Guid; multi-viewpoint QA required.
**23.** [BS] Schemas/visinfo.xsd:98–121 Components, Selection, required Visibility, Coloring; XML schema is distinct from ZIP CRC.
**24.** [B] Documentation/README.md:14–19 GUID vs IfcGuid and :195 meters/degrees; do not confuse with PLN mm.
**25.** [O] TDF ODF Toolkit stable 0.13.0 released 2026-01-23; JDK11, ODF1.2; not named among 61 candidates.
**26.** [OM] Maven Central org.odftoolkit:odfvalidator:0.13.0 is packaging WAR, Apache-2.0; ready CLI binary not proven.
**27.** [OC] ODF Validator checks content/styles/meta/settings XML, manifest, signatures and embedded ODF; not semantic IDS correctness.
**28.** [OS] master Main.java:125–128 supports -1.4; master pom.xml 0.14.0-SNAPSHOT JDK17; cannot attribute to stable 0.13.0.
**29.** [P] PyPI ifcopenshell 0.8.5 Windows wheels 2026-04-13; git ref v0.8.5 404; exact geolocation source signature NOT_VERIFIED.
**30.** [EZ] ezdxf 1.4.5 insert.py:659 mcount/:668 multi_insert; PR165 MINSERT gap confirmed but already known in 18Z, not new candidate.

## Первичные источники и контроль версий
[T] https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp (blob 401de11745903a739dce43a999f7f4df610381c7)
[R] https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp (blob 9f44c2c28da71dee2ff398a34bca18d17451317c)
[I] https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IssueCommands.cpp (blob f7fa0dd39634cbb7545b230ceaf2cc3347c48699)
[TM] https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Sources/IFCCommands.cpp (blob ba390d49a32c04b271f7b5e8486e2b8297a88fa1)
[RM] https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Sources/AddOnMain.cpp (blob d0281e569cbb7f8d647c3fc4959305a6a43a3bae)
[G] https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-5.htm
[GX] https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-33.htm
[B] https://github.com/buildingSMART/BCF-XML/blob/release_2_1/Documentation/README.md
[BV] https://github.com/buildingSMART/BCF-XML/blob/release_2_1/Documentation/bcf.version (blob 000d5b897adf229b9e382dc8f778cbafe6dc5d9d)
[BM] https://github.com/buildingSMART/BCF-XML/blob/release_2_1/Schemas/markup.xsd (blob 037464ee8f6726f1c8ef08fb900a06090fa1d5e6)
[BS] https://github.com/buildingSMART/BCF-XML/blob/release_2_1/Schemas/visinfo.xsd (blob 17f47358273ad998449b0a1090c1fa1749db2351)
[O] https://odftoolkit.org/downloads.html
[OM] https://central.sonatype.com/artifact/org.odftoolkit/odfvalidator/0.13.0
[OC] https://odftoolkit.org/conformance/ODFValidator.html
[OS] https://github.com/tdf/odftoolkit/blob/master/validator/src/main/java/org/odftoolkit/odfvalidator/Main.java (blob 68522c7cb041589a297ba32e777955cf28502fce)
[P] https://pypi.org/project/ifcopenshell/0.8.5/
[EZ] https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py (blob a5c3d621793da3dcd7b292ff6438b94d2c14f005)

**Статусы:** SOURCE verified for exact cited source/ref; installed 1.5.10 not tested. OFFLINE=NOT_RUN, BUILD=NOT_RUN, INSTALLED=NOT_RUN, LIVE=NOT_RUN, ACCEPTED=NO. MODEL_MODE_NOT_VERIFIABLE.