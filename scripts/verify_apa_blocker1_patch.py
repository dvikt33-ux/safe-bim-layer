from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PATCH = REPO_ROOT / "docs" / "research" / "patches" / "tapir-1.5.10-blocker1-readonly-diagnostic.patch"
FILES = ("LibraryCommands.hpp", "LibraryCommands.cpp", "AddOnMain.cpp")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Blocker 1 Tapir source patch against a local source snapshot.")
    parser.add_argument("--source-root", required=True, type=Path, help="Tapir archicad-addon/Sources directory")
    args = parser.parse_args()
    if not PATCH.is_file():
        parser.error(f"patch not found: {PATCH}")
    missing = [name for name in FILES if not (args.source_root / name).is_file()]
    if missing:
        parser.error("source snapshot is missing: " + ", ".join(missing))

    with tempfile.TemporaryDirectory(prefix="apa-blocker1-patch-") as temp:
        root = Path(temp)
        source = root / "archicad-addon" / "Sources"
        source.mkdir(parents=True)
        for name in FILES:
            shutil.copy2(args.source_root / name, source / name)
        subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=root, check=True)
        subprocess.run(["git", "apply", str(PATCH)], cwd=root, check=True)
        header = (source / "LibraryCommands.hpp").read_text(encoding="utf-8-sig")
        implementation = (source / "LibraryCommands.cpp").read_text(encoding="utf-8-sig")
        registration = (source / "AddOnMain.cpp").read_text(encoding="utf-8-sig")
        expected = (
            "ResolveLibraryPartNameDiagnosticCommand",
            "ACAPI_LibraryPart_Search (&probe, false, true)",
            "ACAPI_LibraryPart_GetNum (&partCount)",
            "ACAPI_LibraryPart_Get (&item)",
            'AddList<GS::ObjectState> ("skippedIndices")',
            '"isPlaceable"',
            '"missingDef"',
            '"typeID"',
        )
        combined = header + implementation + registration
        absent = [token for token in expected if token not in combined]
        if absent:
            raise SystemExit("patched source is missing expected diagnostic behavior: " + ", ".join(absent))
        print("PATCH_APPLIES: PASS")
        print("DIAGNOSTIC_SOURCE_CONTRACT: PASS")
        print("LIVE_CALLS: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
