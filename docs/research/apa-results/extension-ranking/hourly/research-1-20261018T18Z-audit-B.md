# APA 18Z — independent counter-audit B: value, duplication, safety
1. No second PDF extractor: PR154 already provides PDFVectors.
2. No second native group writer: CloneNativeGroupV1 exists in PR162; PR164 SceneWriter STOPPED, needs read-only reconciliation.
3. No second IFC/DXF reader: PR165 provides eight IFC and four DXF readers. Missing capabilities are MINSERT expansion, translator provenance and georef roundtrip.
4. ezdxf virtual_entities() alone misses MINSERT copies; XCLIP is ignored and nonuniform TEXT may be wrong. Raw DXF dimensions are not physical construction anchors.
5. Graphisoft AC29 IFC Model Filter can exclude MEP; gross/net export changes opening representation. Absence in IFC does not prove absence in PLN.
6. SAF Excel import/export is not FEM calculation. OCCT triangulated meshes are not original STEP placement matrices.
7. BCF reader is not independent ZIP validator; archived parser is low priority.
8. All scores are expert prioritization, not measured speedups. No 100x benchmark, no changes to main/PLN/APX or canonical plan.
Next: researcher 2 should investigate seven specific ready-tool cards C01–C07 and retain separate SOURCE/OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED gates.
