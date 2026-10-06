# DWG Translator Standard v0.1

Archicad 29 DWG translators are treated as versioned exchange contracts, not as UI preferences.

Three presets are required:

- `DWG_IN_REFERENCE`
- `DWG_OUT_SPDS`
- `DWG_OUT_COMPAT`

## Input

For incoming DWG, the translator must prefer the DWG's own Drawing Unit definition. If the source does not provide a trustworthy unit, the workflow is **blocked until the unit is confirmed**; the builder must not silently assume millimeters merely because that is common in Russian documentation.

Incoming coordination DWG is reference data by default and belongs to the `REF_DWG` workflow, isolated from native priority cleanup.

## SPDS export

`DWG_OUT_SPDS` preserves our semantic Archicad layer structure and uses explicit pen/color, line type and font conversion settings.

PT Astra Sans may remain intact when the recipient receives the font manifest and can legally install the font set.

## Compatibility export

`DWG_OUT_COMPAT` is the fallback for recipients who cannot install project fonts.

Candidate font mapping:

- PT Astra Sans -> Arial
- OpenGost Type B -> Arial

The initial width factor is 1.0 only as a test candidate. It is not released until dimensions, text blocks and titleblock text are visually compared after export.

## Critical round-trip checks

Symbol line types are not assumed to be visually equivalent between Archicad and AutoCAD. Core output therefore relies on simple solid/dashed patterns until a specific symbol line passes export/import tests.

Units, insertion scale, lineweights, text heights, hatches, layer visibility and model/paper-space behavior must all be checked on a real DWG before a translator is marked VERIFIED.

Archicad's Survey Point/georeferencing workflow is handled separately from simple local-model DWG export; no translator may silently move the native building model to large map coordinates.
