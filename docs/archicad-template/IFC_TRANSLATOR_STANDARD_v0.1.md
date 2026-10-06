# IFC Translator Standard v0.1

Archicad 29 supports multiple IFC schemas, so the template must not hard-code one schema as universally correct.

Required presets:

- `IFC_COORD`
- `IFC_ISSUE`
- `IFC_REFERENCE_IMPORT`

## IFC_COORD

For ordinary modern coordination, the starting candidate is **IFC4 / Reference View**, but this remains a project-controlled default. An EIR, BEP or recipient requirement can require IFC2x3 or another supported schema.

Type mapping should continue to use the native Archicad classification / element-type logic as the primary mapping source. The secondary `SBIM Semantic` classification is for our automation and normative semantics and must not silently replace normal IFC type mapping.

Property export is explicit: Core SBIM properties plus active object/module IDS properties are mapped through a controlled preset. We do not export every internal property simply because Archicad can.

## IFC_ISSUE

This preset is intentionally blocked until the project's delivery requirement is known.

Schema, MVD, property set, base quantities and coordinate requirements are contractual data and cannot be inferred safely.

## IFC_REFERENCE_IMPORT

External IFC is a coordination reference by default:

- target workflow: `REF_IFC`
- `SBIM.Core.AutomationState = REFERENCE`
- `SBIM.Core.DataStatus = IMPORTED`
- layer intersection group 0
- no native-edit authority

IFC properties can be mapped into existing Archicad Properties where useful for Graphic Overrides, expressions, collision checks or labels, but only through an explicit mapping.

## Georeferencing

The default candidate for coordination is Survey Point + Project Origin. This keeps the native model near the local Archicad origin while carrying map-coordinate information into exchange.

The actual IFC georeferencing mode must still follow the delivery requirement and must pass a coordinate round-trip check.
