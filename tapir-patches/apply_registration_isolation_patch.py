from __future__ import annotations

import argparse
import shutil
from pathlib import Path

MARKER = "SAFE_BIM_REGISTRATION_ISOLATION_V1"

REGISTER_OLD = r'''template <typename CommandType>
GSErrCode RegisterCommand (CommandGroup& group, const GS::UniString& version, const GS::UniString& description)
{
    GS::Owner<CommandType> command = GS::NewOwned<CommandType> ();
    group.commands.push_back (CommandInfo (
        command->GetName (),
        description,
        version,
        command->GetInputParametersSchema (),
        command->GetRawResponseSchema ())
    );

    GSErrCode err = ACAPI_AddOnAddOnCommunication_InstallAddOnCommandHandler (command.Pass ());
    if (err != NoError) {
        return err;
    }
    return NoError;
}
'''

REGISTER_NEW = r'''// SAFE_BIM_REGISTRATION_ISOLATION_V1
// Diagnostic/fail-soft registration wrapper. A single optional Tapir command
// must not make Archicad unload every command that registered successfully.
// Failures are written to the Archicad report so the exact command can be
// identified. This is intentionally a diagnostic build policy, not an upstream
// behaviour change to merge blindly.
template <typename CommandType>
GSErrCode RegisterCommand (CommandGroup& group, const GS::UniString& version, const GS::UniString& description)
{
    GS::Owner<CommandType> command = GS::NewOwned<CommandType> ();
    const GS::String commandName = command->GetName ();
    group.commands.push_back (CommandInfo (
        commandName,
        description,
        version,
        command->GetInputParametersSchema (),
        command->GetRawResponseSchema ())
    );

    GSErrCode err = ACAPI_AddOnAddOnCommunication_InstallAddOnCommandHandler (command.Pass ());
    if (err != NoError) {
        const GS::UniString printableName (commandName);
        ACAPI_WriteReport (
            "SAFE BIM DIAG: Tapir command registration FAILED: %T, error=%d",
            false,
            printableName.ToPrintf (),
            static_cast<Int32> (err)
        );
        // Keep Initialize alive so already-registered commands remain usable
        // and later commands still get a chance to register.
        return NoError;
    }
    return NoError;
}
'''

REGISTER_INTERFACE_OLD = r'''    return err;
}

GSErrCode Initialize (void)
'''

REGISTER_INTERFACE_NEW = r'''    if (err != NoError) {
        ACAPI_WriteReport (
            "SAFE BIM DIAG: Tapir RegisterInterface had non-zero error=%d; continuing so JSON commands can initialize.",
            false,
            static_cast<Int32> (err)
        );
    }
    return NoError;
}

GSErrCode Initialize (void)
'''

PRECOMMAND_OLD = r'''    err |= TapirPalette::RegisterPaletteControlCallBack ();
    err |= ScriptUIPalette::RegisterPaletteControlCallBack ();

    { // Application Commands
'''

PRECOMMAND_NEW = r'''    err |= TapirPalette::RegisterPaletteControlCallBack ();
    err |= ScriptUIPalette::RegisterPaletteControlCallBack ();

    if (err != NoError) {
        ACAPI_WriteReport (
            "SAFE BIM DIAG: Tapir UI/palette initialization had non-zero error=%d; clearing it before JSON command registration.",
            false,
            static_cast<Int32> (err)
        );
        err = NoError;
    }

    { // Application Commands
'''

FINAL_OLD = r'''    return err;
}

GSErrCode FreeData (void)
'''

FINAL_NEW = r'''    if (err != NoError) {
        ACAPI_WriteReport (
            "SAFE BIM DIAG: Tapir Initialize ended with non-zero error=%d; forcing NoError so successfully registered commands stay loaded.",
            false,
            static_cast<Int32> (err)
        );
    }
    return NoError;
}

GSErrCode FreeData (void)
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to AddOnMain.cpp")
    args = parser.parse_args()

    path = args.source.resolve()
    if not path.exists():
        raise SystemExit(f"Source does not exist: {path}")

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("Registration-isolation patch already applied:", path)
        return 0

    backup = path.with_suffix(path.suffix + ".safe-bim-regdiag.bak")
    if not backup.exists():
        shutil.copy2(path, backup)

    text = replace_once(text, REGISTER_OLD, REGISTER_NEW, "RegisterCommand")
    text = replace_once(text, REGISTER_INTERFACE_OLD, REGISTER_INTERFACE_NEW, "RegisterInterface return")
    text = replace_once(text, PRECOMMAND_OLD, PRECOMMAND_NEW, "Initialize pre-command block")
    text = replace_once(text, FINAL_OLD, FINAL_NEW, "Initialize final return")

    path.write_text(text, encoding="utf-8", newline="\n")
    print("REGISTRATION ISOLATION PATCH PASS")
    print("Source:", path)
    print("Backup:", backup)
    print("Policy: log individual failures, keep successful JSON commands loaded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
