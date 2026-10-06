# Master Layout / Form 3 blueprint v0.1

The geometry is now based on the actual 2026 standard, not on a legacy titleblock copied from another template.

Confirmed for working-drawing / graphical-document sheets:

- titleblock: **Form 3** of GOST R 21.101-2026;
- position: bottom-right;
- titleblock overall size: **185 × 55 mm**;
- main horizontal division: **65 + 120 mm**;
- left titleblock columns: **10 / 10 / 10 / 10 / 15 / 10 mm**;
- right major widths: **70 + 50 mm**;
- sheet inner frame: **20 mm left, 5 mm top, 5 mm right, 5 mm bottom**; the standard figure also shows **10 mm** as an allowed lower-frame dimension;
- A4 titleblock is placed along the short side; larger sheets normally use the long side.

The canonical graph meanings 1–27 are stored in `master-layout-form3-registry-v0.1.yaml`.

## Automation status

Tapir 1.5.8 exposes enough pieces to attempt Master Layout geometry creation:

- `CreateLayout`
- `GetNavigatorItemTree`
- `GetDatabaseIdFromNavigatorItemId`
- `ChangeWindow` with `MasterLayout`
- `CreateLineElements`
- `CreateTexts`

Therefore the frame/titleblock **geometry is no longer considered a permanent manual gap**.

The remaining blocker is general Archicad AutoText insertion. `CreateTexts` supports plain text, but this Tapir schema has no general command for enumerating/inserting Project Info/Layout AutoText tokens. We will not hard-code sheet numbers, sheet counts, scale, project name or signatures as ordinary static text merely to make the titleblock look complete.

Next live test:
1. create one sacrificial A3 master/layout;
2. switch to its Master Layout database;
3. draw a minimal rectangle and one test text;
4. read back / visually inspect;
5. only after PASS generate the full Form 3 grid.
