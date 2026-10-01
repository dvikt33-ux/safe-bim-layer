from __future__ import annotations

import argparse
import shutil
from pathlib import Path

MARKER = "SAFE_BIM_HOSTED_LIBRARY_PART_NAME_V1"

HELPER = r'''
// SAFE_BIM_HOSTED_LIBRARY_PART_NAME_V1
// Resolve an explicitly requested hosted Window/Door library part by its
// document name and make the freshly prepared element/memo consistent with it.
// favoriteName remains useful for marker and other defaults. This helper is
// intentionally called AFTER PrepareWindowOrDoorDefaults, so libraryPartName
// is the final authority for the hosted GDL part while explicit width/height
// and placement fields, applied later, still override A/B defaults.
//
// Replacing only openingBase.libInd is unsafe: memo.params would still belong
// to the previously active Window/Door part. Fetch and install the requested
// part's own parameters at the same time.
GSErrCode ApplyWindowOrDoorLibraryPartByName (
    const GS::ObjectState& data,
    API_ElemTypeID elemTypeId,
    API_Element& element,
    API_ElementMemo& memo)
{
    GS::UniString libraryPartName;
    if (!data.Get ("libraryPartName", libraryPartName) || libraryPartName.IsEmpty ()) {
        return NoError;
    }

    API_LibPart libPart = {};
    GS::ucscpy (libPart.docu_UName, libraryPartName.ToUStr ());

    GSErrCode err = ACAPI_LibraryPart_Search (&libPart, false, true);
    const GS::OnExit locationGuard ([&] () { delete libPart.location; });
    if (err != NoError) {
        return err;
    }

    const API_LibTypeID expectedType =
        elemTypeId == API_WindowID ? APILib_WindowID : APILib_DoorID;
    if (libPart.typeID != expectedType) {
        return APIERR_BADID;
    }

    double a = 0.0;
    double b = 0.0;
    Int32 addParNum = 0;
    API_AddParType** addPars = nullptr;
    err = ACAPI_LibraryPart_GetParams (libPart.index, &a, &b, &addParNum, &addPars);
    if (err != NoError) {
        return err;
    }

    if (memo.params != nullptr) {
        BMKillHandle (reinterpret_cast<GSHandle*> (&memo.params));
    }
    memo.params = addPars;

    element.window.openingBase.libInd = libPart.index;
    element.window.openingBase.width = a;
    element.window.openingBase.height = b;
    return NoError;
}

'''

WINDOW_SCHEMA_OLD = r'''                        "favoriteName": {
                            "type": "string",
                            "description": "Optional. Name of an existing Window favorite (as returned by `GetFavoritesByType`). Applied to the Window tool defaults before the create."
                        }
'''
WINDOW_SCHEMA_NEW = r'''                        "favoriteName": {
                            "type": "string",
                            "description": "Optional. Name of an existing Window favorite (as returned by `GetFavoritesByType`). Applied to the Window tool defaults before the create."
                        },
                        "libraryPartName": {
                            "type": "string",
                            "description": "Optional. Exact document name of a Window library part. Applied after tool defaults/favorite selection and before explicit width/height/placement overrides."
                        }
'''

DOOR_SCHEMA_OLD = r'''                        "favoriteName": {
                            "type": "string",
                            "description": "Optional. Name of an existing Door favorite (as returned by `GetFavoritesByType`). Applied to the Door tool defaults before the create."
                        }
'''
DOOR_SCHEMA_NEW = r'''                        "favoriteName": {
                            "type": "string",
                            "description": "Optional. Name of an existing Door favorite (as returned by `GetFavoritesByType`). Applied to the Door tool defaults before the create."
                        },
                        "libraryPartName": {
                            "type": "string",
                            "description": "Optional. Exact document name of a Door library part. Applied after tool defaults/favorite selection and before explicit width/height/placement overrides."
                        }
'''

WINDOW_PREP_OLD = r'''            err = PrepareWindowOrDoorDefaults (API_WindowID, element, memo, marker);
            if (err != NoError) {
                elements.Push (CreateErrorResponse (err, "Failed to prepare window defaults."));
                continue;
            }

            double centerOffset = 0.0;
'''
WINDOW_PREP_NEW = r'''            err = PrepareWindowOrDoorDefaults (API_WindowID, element, memo, marker);
            if (err != NoError) {
                elements.Push (CreateErrorResponse (err, "Failed to prepare window defaults."));
                continue;
            }

            err = ApplyWindowOrDoorLibraryPartByName (data, API_WindowID, element, memo);
            if (err != NoError) {
                elements.Push (CreateErrorResponse (err, "Failed to resolve `libraryPartName` for window or the requested part is not Window-compatible."));
                continue;
            }

            double centerOffset = 0.0;
'''

DOOR_PREP_OLD = r'''            err = PrepareWindowOrDoorDefaults (API_DoorID, element, memo, marker);
            if (err != NoError) {
                elements.Push (CreateErrorResponse (err, "Failed to prepare door defaults."));
                continue;
            }

            double centerOffset = 0.0;
'''
DOOR_PREP_NEW = r'''            err = PrepareWindowOrDoorDefaults (API_DoorID, element, memo, marker);
            if (err != NoError) {
                elements.Push (CreateErrorResponse (err, "Failed to prepare door defaults."));
                continue;
            }

            err = ApplyWindowOrDoorLibraryPartByName (data, API_DoorID, element, memo);
            if (err != NoError) {
                elements.Push (CreateErrorResponse (err, "Failed to resolve `libraryPartName` for door or the requested part is not Door-compatible."));
                continue;
            }

            double centerOffset = 0.0;
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one upstream match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to ExtendedElementCommands.cpp")
    args = parser.parse_args()

    path = args.source.resolve()
    if not path.exists():
        raise SystemExit(f"Source file does not exist: {path}")

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("Hosted library-part patch already applied:", path)
        return 0

    favorite_anchor = "// Apply a named FAVORITE to the Door/Window tool defaults BEFORE"
    if text.count(favorite_anchor) != 1:
        raise RuntimeError("Could not locate the Window/Door favorite helper anchor exactly once")

    backup = path.with_suffix(path.suffix + ".safe-bim-libpart.bak")
    if not backup.exists():
        shutil.copy2(path, backup)

    text = text.replace(favorite_anchor, HELPER + favorite_anchor, 1)
    text = replace_once(text, WINDOW_SCHEMA_OLD, WINDOW_SCHEMA_NEW, "Window schema")
    text = replace_once(text, DOOR_SCHEMA_OLD, DOOR_SCHEMA_NEW, "Door schema")
    text = replace_once(text, WINDOW_PREP_OLD, WINDOW_PREP_NEW, "Window create path")
    text = replace_once(text, DOOR_PREP_OLD, DOOR_PREP_NEW, "Door create path")

    path.write_text(text, encoding="utf-8", newline="\n")

    print("PATCH PASS")
    print("Source:", path)
    print("Backup:", backup)
    print("Added: CreateWindows.windowsData[].libraryPartName")
    print("Added: CreateDoors.doorsData[].libraryPartName")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
