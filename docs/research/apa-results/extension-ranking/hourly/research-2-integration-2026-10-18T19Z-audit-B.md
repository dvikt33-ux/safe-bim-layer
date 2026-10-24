# Researcher 2 19Z — two independent counteraudits

## A. Source, version, API/ABI, licenses
A1. Re-read Tapir IFCCommands.cpp **tag 1.5.9**: IFC IDs support 0..N and externalIFCId; **tag 1.6.0** alone exposes GetIFCExportTranslators name/preview. Local 1.5.10 runtime port 19724 receipt confirms version but not binary hash or backported command. Do not infer local availability.
A2. PR164 reconciliation blob 0e4a3514 at 19:09Z independently compared with reconciler source b156ae37 and STOPPED receipt fd9caf32. 44 GUID/BREP and zero dispatch are scoped to that attempt; otherActorsNotCovered=true. No Clone retry.
A3. PR165 source blob 39b8b604 and synthetic installed-smoke blob 92c664ef distinguish code contract, prior installed receipt, and LIVE. MINSERT expansion not implemented. Samples 5000 and source cap 4GiB are not full-model QA.
A4. PR166 B1 source blob 98573f07 pins ifcopenshell/ifctester 0.8.5, checks ODS ZIP only. TDF ODF Validator 0.13.0 requires JRE11+ and dependency jar; no local jar, installed JDK, or transitive license lock. Graphisoft SDK29 proprietary; Tapir/ezdxf MIT; TDF ODF validator Apache-2.0; upstream BCF Python file LGPL-3.0-or-later; buildingSMART BCF-XML release_2_1 license NOT_VERIFIED (LICENSE 404).
A5. IfcOpenShell commit b139fe1c geolocation/BCF source is NOT proof of exact installed 0.8.5. SDK30 never substituted for SDK29. MODEL_MODE_NOT_VERIFIABLE.

## B. Mounting graph, duplication, engineering value and safety
B1. Keep one chain: APA Router/Bridge → existing Tapir command or PR165/PR166 local provider → ready ezdxf/IfcOpenShell/ODF validator → read-only artifact. Maximum three external links; do not add second writer, IFC engine, PDF parser, BIM Graph or SceneWriter.
B2. Compare paths: native Tapir ExportIssuesToBCF handles Archicad Issues but empty selection exports ALL and local version unverified; IfcTester BCF2 handles IDS failures on IFC without native write. Choose according to origin, not a universal BCF adapter. BCF ZIP is not JSON; parse separately.
B3. ODS: B1 ZIP CRC checks transport, TDF Validator checks ODF schema. Choose both in series after installation approval. No web upload of project ODS.
B4. DXF: hand-written MINSERT expansion duplicates ezdxf; prefer multi_insert, preserve OCS/WCS and $INSUNITS, warn XCLIP/nonuniform. Six-point 2×3 fixture is SPECIFIED, NOT EXECUTED.
B5. IFC: GetElementsByIFCIds can return 0..N; Merge changes GlobalId. Store native GUID, ifcId, externalIFCId, source IFC SHA, translator preset provenance; missing exported opening does not prove missing native opening.
B6. No speedup claims. Gate SOURCE→OFFLINE fixture/SHA→BUILD (approval)→INSTALLED binary hash→LIVE approved scratch→ACCEPTED independent readback. This cycle SOURCE only; no changes to main/PLN/APX/code/queue/plan182.
