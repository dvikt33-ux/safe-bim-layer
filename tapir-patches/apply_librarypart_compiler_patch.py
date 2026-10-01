from __future__ import annotations

import argparse
import shutil
from pathlib import Path

MARKER = "SAFE_BIM_LIBRARY_PART_COMPILER_V1"

HEADER_CLASS = r'''

// SAFE_BIM_LIBRARY_PART_COMPILER_V1
class CreateLibraryPartFromScriptsCommand : public CommandBase
{
public:
    CreateLibraryPartFromScriptsCommand ();
    virtual GS::String GetName () const override;
    virtual GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    virtual GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    virtual GS::ObjectState Execute (const GS::ObjectState& parameters, GS::ProcessControl& processControl) const override;
};
'''

CPP_IMPL = r'''

// ============================================================================
// SAFE_BIM_LIBRARY_PART_COMPILER_V1
// Creates a real Archicad Library Part directly from textual GDL sections.
// First implementation intentionally supports the three most important
// placeable model-component routes: Window, Door and Object.
//
// Window/Door subtype ancestry and parameter/detail defaults are inherited
// from the current Archicad tool default. This avoids hard-coding Graphisoft
// subtype GUIDs and keeps the generated part compatible with the installed
// Archicad version/library environment.
// ============================================================================

namespace {

bool ParseSafeBimLibraryPartType (const GS::UniString& typeName, API_LibTypeID& libType, API_ElemTypeID& toolType)
{
    if (typeName == "Window") {
        libType = APILib_WindowID;
        toolType = API_WindowID;
        return true;
    }
    if (typeName == "Door") {
        libType = APILib_DoorID;
        toolType = API_DoorID;
        return true;
    }
    if (typeName == "Object") {
        libType = APILib_ObjectID;
        toolType = API_ObjectID;
        return true;
    }
    return false;
}

GSErrCode GetPrototypeLibraryPartForTool (
    API_LibTypeID libType,
    API_ElemTypeID toolType,
    API_LibPart& prototype,
    API_LibPartDetails& details,
    API_AddParType*** addPars)
{
    API_Element element = {};
    API_ElementMemo memo = {};
    API_SubElement marker = {};
#ifdef ServerMainVers_2600
    element.header.type = toolType;
#else
    element.header.typeID = toolType;
#endif

    GSErrCode err = NoError;
    Int32 libInd = 0;

    if (toolType == API_WindowID || toolType == API_DoorID) {
        marker.subType = APISubElement_MainMarker;
        err = ACAPI_Element_GetDefaultsExt (&element, &memo, 1UL, &marker);
        if (err == NoError) {
            libInd = toolType == API_WindowID
                ? element.window.openingBase.libInd
                : element.door.openingBase.libInd;
        }
        ACAPI_DisposeElemMemoHdls (&marker.memo);
    } else {
        err = ACAPI_Element_GetDefaults (&element, &memo);
        if (err == NoError) {
            libInd = element.object.libInd;
        }
    }
    ACAPI_DisposeElemMemoHdls (&memo);

    if (err != NoError) {
        return err;
    }
    if (libInd <= 0) {
        return APIERR_MISSINGDEF;
    }

    prototype = {};
    prototype.index = libInd;
    err = ACAPI_LibraryPart_Get (&prototype);
    if (err != NoError) {
        return err;
    }

    double prototypeA = 0.0;
    double prototypeB = 0.0;
    Int32 addParNum = 0;
    *addPars = nullptr;
    err = ACAPI_LibraryPart_GetParams (prototype.index, &prototypeA, &prototypeB, &addParNum, addPars);
    if (err != NoError) {
        return err;
    }

    details = {};
    err = ACAPI_LibPart_GetDetails (prototype.index, &details);
    if (err != NoError) {
        ACAPI_DisposeAddParHdl (addPars);
        *addPars = nullptr;
        return err;
    }

    if (prototype.typeID != libType) {
        ACAPI_DisposeAddParHdl (addPars);
        *addPars = nullptr;
        return APIERR_BADID;
    }

    return NoError;
}

GS::ObjectState MakeSafeBimLibraryPartResult (const API_LibPart& libPart, const GS::UniString& typeName, bool alreadyExisted)
{
    GS::ObjectState result;
    result.Add ("index", static_cast<Int32> (libPart.index));
    result.Add ("documentName", GS::UniString (libPart.docu_UName));
    result.Add ("typeId", typeName);
    result.Add ("alreadyExisted", alreadyExisted);
    return result;
}

} // namespace

CreateLibraryPartFromScriptsCommand::CreateLibraryPartFromScriptsCommand () :
    CommandBase (CommonSchema::Used)
{
}

GS::String CreateLibraryPartFromScriptsCommand::GetName () const
{
    return "CreateLibraryPartFromScripts";
}

GS::Optional<GS::UniString> CreateLibraryPartFromScriptsCommand::GetInputParametersSchema () const
{
    return R"({
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["Window", "Door", "Object"],
                "description": "Library Part semantic type."
            },
            "name": {
                "type": "string",
                "description": "Document name of the new Library Part."
            },
            "a": {
                "type": "number",
                "exclusiveMinimum": 0,
                "description": "Default A parameter (width)."
            },
            "b": {
                "type": "number",
                "exclusiveMinimum": 0,
                "description": "Default B parameter (height/depth depending on subtype)."
            },
            "script2D": {
                "type": "string",
                "description": "Optional GDL 2D script."
            },
            "script3D": {
                "type": "string",
                "description": "Required GDL 3D script."
            },
            "returnExisting": {
                "type": "boolean",
                "description": "If a Library Part with the same document name already exists, return it instead of failing. Default true."
            }
        },
        "additionalProperties": false,
        "required": ["type", "name", "a", "b", "script3D"]
    })";
}

GS::Optional<GS::UniString> CreateLibraryPartFromScriptsCommand::GetRawResponseSchema () const
{
    return R"({
        "type": "object",
        "properties": {
            "libraryPart": {
                "type": "object",
                "properties": {
                    "index": { "type": "integer" },
                    "documentName": { "type": "string" },
                    "typeId": { "type": "string" },
                    "alreadyExisted": { "type": "boolean" }
                },
                "required": ["index", "documentName", "typeId", "alreadyExisted"]
            }
        },
        "required": ["libraryPart"]
    })";
}

GS::ObjectState CreateLibraryPartFromScriptsCommand::Execute (const GS::ObjectState& parameters, GS::ProcessControl& /*processControl*/) const
{
    GS::UniString typeName;
    GS::UniString name;
    GS::UniString script2D;
    GS::UniString script3D;
    double a = 0.0;
    double b = 0.0;
    bool returnExisting = true;

    if (!parameters.Get ("type", typeName) ||
        !parameters.Get ("name", name) || name.IsEmpty () ||
        !parameters.Get ("a", a) || a <= 0.0 ||
        !parameters.Get ("b", b) || b <= 0.0 ||
        !parameters.Get ("script3D", script3D) || script3D.IsEmpty ()) {
        return CreateErrorResponse (APIERR_BADPARS, "Missing or invalid type/name/a/b/script3D.");
    }
    parameters.Get ("script2D", script2D);
    parameters.Get ("returnExisting", returnExisting);

    API_LibTypeID libType = APILib_ObjectID;
    API_ElemTypeID toolType = API_ObjectID;
    if (!ParseSafeBimLibraryPartType (typeName, libType, toolType)) {
        return CreateErrorResponse (APIERR_BADPARS, "Unsupported Library Part type. Use Window, Door or Object.");
    }

    // A same-name part is reusable. This is deliberate: component compilation
    // becomes idempotent and Safe BIM can cache parts between generation passes.
    API_LibPart existing = {};
    existing.typeID = libType;
    GS::ucscpy (existing.docu_UName, name.ToUStr ());
    GSErrCode searchErr = ACAPI_LibraryPart_Search (&existing, false, true);
    const bool exists = searchErr == NoError && existing.index > 0 && existing.typeID == libType;
    if (exists) {
        GS::ObjectState response;
        response.Add ("libraryPart", MakeSafeBimLibraryPartResult (existing, typeName, true));
        delete existing.location;
        return response;
    }
    delete existing.location;
    if (!returnExisting && searchErr == NoError) {
        return CreateErrorResponse (APIERR_BADNAME, "A Library Part with this name already exists.");
    }

    API_LibPart prototype = {};
    API_LibPartDetails details = {};
    API_AddParType** addPars = nullptr;
    GSErrCode err = GetPrototypeLibraryPartForTool (libType, toolType, prototype, details, &addPars);
    if (err != NoError) {
        delete prototype.location;
        return CreateErrorResponse (err, "Could not derive Library Part subtype/default parameters from the current Archicad tool defaults.");
    }
    const GS::OnExit prototypeCleanup ([&] () {
        delete prototype.location;
        if (addPars != nullptr) {
            ACAPI_DisposeAddParHdl (&addPars);
        }
    });

    auto folderId = API_SpecFolderID::API_EmbeddedProjectLibraryFolderID;
    IO::Location embeddedLibraryFolder;
    if (ACAPI_ProjectSettings_GetSpecFolder (&folderId, &embeddedLibraryFolder) != NoError ||
        IO::Folder (embeddedLibraryFolder).GetStatus () != NoError) {
        return CreateErrorResponse (APIERR_NOLIB, "Could not resolve the Embedded Library folder.");
    }

    API_LibPart libPart = {};
    libPart.typeID = libType;
    libPart.isTemplate = false;
    libPart.isPlaceable = true;
    libPart.location = &embeddedLibraryFolder;
    GS::ucscpy (libPart.docu_UName, name.ToUStr ());
    GS::ucscpy (libPart.file_UName, name.ToUStr ());
    CHCopyC (prototype.parentUnID, libPart.parentUnID);

    GSHandle paramsHdl = nullptr;
    err = ACAPI_LibPart_GetSect_ParamDef (&libPart, addPars, &a, &b, nullptr, &paramsHdl);
    if (err != NoError) {
        return CreateErrorResponse (err, "Failed to build Library Part parameter section.");
    }
    const GS::OnExit paramsCleanup ([&] () { BMKillHandle (&paramsHdl); });

    err = ACAPI_LibPart_SetDetails_ParamDef (&libPart, paramsHdl, &details);
    if (err != NoError) {
        return CreateErrorResponse (err, "Failed to apply inherited Library Part details.");
    }

    err = ACAPI_LibPart_Create (&libPart);
    if (err != NoError) {
        return CreateErrorResponse (err, "ACAPI_LibPart_Create failed.");
    }

    // After Create succeeds, Save must always be called to close the scratch
    // Library Part, even when a section write fails.
    GSErrCode sectionErr = NoError;

    API_LibPartSection section = {};
    section.sectType = API_SectParamDef;
    sectionErr = ACAPI_LibPart_AddSection (&section, paramsHdl, nullptr);

    if (sectionErr == NoError && !script2D.IsEmpty ()) {
        section = {};
        section.sectType = API_Sect2DScript;
        sectionErr = ACAPI_LibPart_AddSection (&section, nullptr, &script2D);
    }

    if (sectionErr == NoError) {
        section = {};
        section.sectType = API_Sect3DScript;
        sectionErr = ACAPI_LibPart_AddSection (&section, nullptr, &script3D);
    }

    const GSErrCode saveErr = ACAPI_LibPart_Save (&libPart);
    if (sectionErr != NoError) {
        return CreateErrorResponse (sectionErr, "Failed to add a Library Part section.");
    }
    if (saveErr != NoError) {
        return CreateErrorResponse (saveErr, "ACAPI_LibPart_Save failed.");
    }

    // Resolve again by document name; Save registers the part, and the search
    // gives us the authoritative index returned by Archicad's library system.
    API_LibPart saved = {};
    saved.typeID = libType;
    GS::ucscpy (saved.docu_UName, name.ToUStr ());
    err = ACAPI_LibraryPart_Search (&saved, false, true);
    if (err != NoError || saved.index <= 0) {
        delete saved.location;
        return CreateErrorResponse (err != NoError ? err : APIERR_MISSINGDEF, "Library Part was saved but could not be resolved afterwards.");
    }

    GS::ObjectState response;
    response.Add ("libraryPart", MakeSafeBimLibraryPartResult (saved, typeName, false));
    delete saved.location;
    return response;
}
'''

REGISTRATION_OLD = r'''        err |= RegisterCommand<GetAvailableLibraryPartsCommand> (
            libraryCommands, "1.5.0",
            "Lists library parts currently available to the project. Filter by typeId (e.g. 'Door', 'Window', 'Object', 'Lamp')."
        );
        AddCommandGroup (libraryCommands);
'''

REGISTRATION_NEW = r'''        err |= RegisterCommand<GetAvailableLibraryPartsCommand> (
            libraryCommands, "1.5.0",
            "Lists library parts currently available to the project. Filter by typeId (e.g. 'Door', 'Window', 'Object', 'Lamp')."
        );
        err |= RegisterCommand<CreateLibraryPartFromScriptsCommand> (
            libraryCommands, "1.5.9-safe-bim.1",
            "Creates a real Window, Door or Object Library Part from textual 2D/3D GDL scripts using Archicad's native Library Part API."
        );
        AddCommandGroup (libraryCommands);
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", type=Path, help="Path to archicad-addon/Sources")
    args = parser.parse_args()

    sources = args.sources.resolve()
    header = sources / "LibraryCommands.hpp"
    cpp = sources / "LibraryCommands.cpp"
    addon = sources / "AddOnMain.cpp"

    for path in (header, cpp, addon):
        if not path.exists():
            raise SystemExit(f"Missing source file: {path}")

    if MARKER in header.read_text(encoding="utf-8"):
        print("Library Part compiler patch already applied")
        return 0

    for path in (header, cpp, addon):
        backup = path.with_suffix(path.suffix + ".safe-bim-libpart-compiler.bak")
        if not backup.exists():
            shutil.copy2(path, backup)

    h = header.read_text(encoding="utf-8")
    h = h.rstrip() + HEADER_CLASS + "\n"
    header.write_text(h, encoding="utf-8", newline="\n")

    c = cpp.read_text(encoding="utf-8")
    c = c.rstrip() + CPP_IMPL + "\n"
    cpp.write_text(c, encoding="utf-8", newline="\n")

    a = addon.read_text(encoding="utf-8")
    if a.count(REGISTRATION_OLD) != 1:
        raise RuntimeError(f"AddOnMain registration anchor count={a.count(REGISTRATION_OLD)}")
    a = a.replace(REGISTRATION_OLD, REGISTRATION_NEW, 1)
    addon.write_text(a, encoding="utf-8", newline="\n")

    print("LIBRARY PART COMPILER PATCH PASS")
    print("Added command: CreateLibraryPartFromScripts")
    print("Supported types: Window, Door, Object")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
