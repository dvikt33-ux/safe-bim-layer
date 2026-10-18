# APA №1 19Z — два независимых контрааудита

## Аудит A: первичность, версия, совместимость
1. Tapir exact ref 1.5.9: AddOnMain blob 9f44c2c28da71dee2ff398a34bca18d17451317c, IFCCommands blob 401de11745903a739dce43a999f7f4df610381c7, IssueCommands blob f7fa0dd39634cbb7545b230ceaf2cc3347c48699. Командные версии 1.5.1/1.0.6 не версия бинарника. Local 1.5.10 NOT_VERIFIED.
2. Upstream main AddOnMain blob d0281e569cbb7f8d647c3fc4959305a6a43a3bae: GetIFCExportTranslators introduced 1.6.0; ref 1.5.9 отсутствует. main IFCCommands blob ba390d49a32c04b271f7b5e8486e2b8297a88fa1 returns only name/preview, not 6 presets.
3. Graphisoft official AC29 IFC Import, not AC28/30, confirms regenerated GlobalId after Merge and External IFC ID. Opera fresh tab readback PASS; closed only created tab.
4. BCF release_2_1: bcf.version blob 000d5b897adf229b9e382dc8f778cbafe6dc5d9d; markup.xsd 037464ee8f6726f1c8ef08fb900a06090fa1d5e6; visinfo.xsd 17f47358273ad998449b0a1090c1fa1749db2351. Root README says BCF2.0 (stale). LICENSE 404 in release_2_1; main LICENSE CC BY-ND 4.0, not transferable without provenance.
5. TDF ODF stable 0.13.0 released 2026-01-23 JDK11/ODF1.2, Maven WAR. Master pom 0.14.0-SNAPSHOT JDK17, Main.java -1.4; do not attribute master API to stable.
6. PyPI IfcOpenShell 0.8.5 Windows wheel exists, GitHub v0.8.5 404; v0.8.0 geolocation source is NOT exact 0.8.5 API proof.

## Аудит B: инженерная польза, дублирование, риски
1. Tapir IFC bidirectional mapping already solves F18-03 at SOURCE; no second IFC mapper. However mapping may be 0..N and Merge changes GlobalId. Require read-only validation.
2. Tapir BCF exporter is ready source; empty issues exports ALL. No implicit mass export. ImportIssuesFromBCF is MODEL WRITE and prohibited.
3. BCF XSD alone does not validate ZIP links, PNG, .bcfv, IFC component existence or Survey Point. ZIP CRC alone is insufficient.
4. ODF Validator 0.13.0 covers PR166 B1 schema gap; stable supports ODF1.2 only, JDK11 availability unknown, no install.
5. Graphisoft six presets vs Tapir list name+preview: full programmatic preset serialization NOT_FOUND in checked source; do not promise.
6. ezdxf MINSERT is already found in 18Z, not a new candidate. Do not duplicate PR154/162/165/166. No 100x benchmark or ACCEPTED.

Residual blockers: local Tapir port/version, BCF release_2_1 license, ODF binary/Java, pinned IfcOpenShell 0.8.5 georef source, IFC translator full presets. Both audits documentary, not LIVE tests.