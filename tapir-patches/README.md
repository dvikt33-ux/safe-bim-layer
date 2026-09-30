# Tapir patches for Safe BIM universal library system

This directory tracks the minimal Tapir changes required by the Library-First architecture.

The first patch target is **explicit library-part selection for hosted Window/Door creation**. Tapir already resolves `libraryPartName` for Objects/Lamps and already imports/registers embedded library files of multiple native types. We should reuse those mechanisms rather than build a parallel library manager.

## Patch contract

`CreateWindows.windowsData[]` and `CreateDoors.doorsData[]` gain:

```json
"libraryPartName": "SB_Gothic_Lancet_Large_v01"
```

Resolution order:

1. read tool defaults;
2. apply `favoriteName` when provided;
3. resolve and apply `libraryPartName` when provided;
4. apply explicit size/placement/orientation overrides;
5. create hosted element;
6. verify read-back `libPart.name`.

The patch must validate compatibility and fail closed instead of silently placing the wrong library part.

## Why this is generic

The same component router will later route assets to the correct native mechanism:

- hosted Window/Door/Skylight parts -> GSM library part;
- reusable free-standing detail -> Object;
- nested helper -> Macro;
- light -> Lamp;
- continuous moulding/metal section -> Profile attribute;
- material/finish/build-up -> native attributes;
- repeated building assembly -> Hotlink Module.

Do not force Profile attributes, materials or Hotlink Modules into GSM merely because they are reusable.