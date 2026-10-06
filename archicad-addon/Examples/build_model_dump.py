"""Build the native Model Dump v1 overlay without modifying the Tapir checkout."""
import argparse
import os
import shutil
import subprocess
import tarfile
from pathlib import Path


def latest_subdir(path):
    path = Path(path)
    if not path.is_dir():
        return None
    dirs = [p for p in path.iterdir() if p.is_dir()]
    return max(dirs, key=lambda p: p.name) if dirs else None


def resolve_toolchain(args):
    vc = Path(args.vc) if args.vc else None
    if vc is None and os.environ.get("VCToolsInstallDir"):
        vc = Path(os.environ["VCToolsInstallDir"])
    if vc is None:
        roots = [Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) /
                 "Microsoft Visual Studio"]
        candidates = []
        for root in roots:
            candidates.extend(root.glob("*/*/VC/Tools/MSVC/*"))
        candidates = [p for p in candidates if (p / "bin" / "Hostx64" / "x64" / "nmake.exe").exists()]
        vc = max(candidates, key=lambda p: p.name) if candidates else None
    sdk_root = Path(args.sdk_root) if args.sdk_root else Path(
        os.environ.get("WindowsSdkDir", r"C:\Program Files (x86)\Windows Kits\10"))
    sdk_version = args.sdk_version or os.environ.get("WindowsSDKVersion", "").strip("\\/")
    if not sdk_version:
        selected = latest_subdir(sdk_root / "Include")
        sdk_version = selected.name if selected else None
    cmake = args.cmake or shutil.which("cmake")
    if not cmake:
        raise RuntimeError("CMake not found; install CMake or pass --cmake")
    if vc is None or not (vc / "bin" / "Hostx64" / "x64" / "nmake.exe").exists():
        raise RuntimeError("MSVC toolset not found; pass --vc with its VC/Tools/MSVC/<version> path")
    if not sdk_version or not (sdk_root / "Include" / sdk_version).is_dir():
        raise RuntimeError("Windows SDK not found; pass --sdk-root and optionally --sdk-version")
    return vc, sdk_root, sdk_version, cmake


def overlay_registration(addon_source):
    addon_source = Path(addon_source)
    main_cpp = addon_source / "Sources" / "AddOnMain.cpp"
    text = main_cpp.read_text(encoding="utf-8")

    include_line = '#include "ModelDumpCommands.hpp"'
    include_anchor = '#include "ElementCommands.hpp"\n'
    if include_line not in text:
        if text.count(include_anchor) != 1:
            raise RuntimeError("Could not locate the unique ElementCommands include in AddOnMain.cpp")
        text = text.replace(include_anchor, include_anchor + include_line + "\n", 1)

    model_register = ('        err |= RegisterCommand<GetModelDumpV1Command> (elementCommands, "model-dump-v1", '
                      '"Dump all available regenerated resultant 3D bodies, stories, native bindings and effective face materials.");')
    if model_register not in text:
        group_anchor = "        err |= RegisterCommand<GetCurrent2DDocumentV1Command> (elementCommands, "document-2d-v1", "Read current-database Line and Text geometry/content, including raw and interpreted AutoText, without modifying project elements.");
        AddCommandGroup (elementCommands);"
        if text.count(group_anchor) != 1:
            raise RuntimeError("Could not locate the unique elementCommands registration group")
        text = text.replace(group_anchor, model_register + "\n" + group_anchor, 1)

    autotext_register = ('        err |= RegisterCommand<GetAutoTextsV1Command> (projectCommands, "autotext-v1", '
                         '"Enumerate current Archicad AutoText description/key/value triplets without modifying the project.");')
    if autotext_register not in text:
        project_anchor = "        AddCommandGroup (projectCommands);"
        if text.count(project_anchor) != 1:
            raise RuntimeError("Could not locate the unique projectCommands registration group")
        text = text.replace(project_anchor, autotext_register + "\n" + project_anchor, 1)

    main_cpp.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tapir-repo", required=True, help="Clean or dirty Tapir Git checkout; only git archive of --ref is copied")
    parser.add_argument("--ref", default="HEAD", help="Tapir Git ref to build from")
    parser.add_argument("--devkit", required=True, help="Archicad DevKit Support directory")
    parser.add_argument("--build", required=True, help="Build/output directory; generated files stay here")
    parser.add_argument("--vc", help="MSVC VC/Tools/MSVC/<version> path; otherwise auto-detected")
    parser.add_argument("--sdk-root", help="Windows Kits/10 root; otherwise auto-detected")
    parser.add_argument("--sdk-version", help="Windows SDK version; otherwise latest installed is used")
    parser.add_argument("--cmake", help="CMake executable; otherwise PATH lookup is used")
    args = parser.parse_args()

    tapir_repo = Path(args.tapir_repo).resolve()
    if not (tapir_repo / ".git").exists():
        raise RuntimeError(f"--tapir-repo must be a Git checkout: {tapir_repo}")
    build_root = Path(args.build).resolve()
    build_root.mkdir(parents=True, exist_ok=True)
    overlay_root = (build_root / "source").resolve()
    if overlay_root == tapir_repo or tapir_repo in overlay_root.parents:
        raise RuntimeError("Build source must not be inside or replace the supplied Tapir checkout")
    if overlay_root.exists():
        shutil.rmtree(overlay_root)
    overlay_root.mkdir(parents=True)
    archive = build_root / "tapir-source.tar"
    with archive.open("wb") as output:
        subprocess.run(["git", "-c", f"safe.directory={tapir_repo}", "-C", str(tapir_repo),
                        "archive", "--format=tar", args.ref],
                       stdout=output, check=True)
    with tarfile.open(archive, "r") as tar:
        tar.extractall(overlay_root)
    archive.unlink()
    addon_source = overlay_root / "archicad-addon"
    if not (addon_source / "CMakeLists.txt").exists():
        raise RuntimeError(f"Tapir ref {args.ref!r} has no archicad-addon/CMakeLists.txt")
    addon_overlay = Path(__file__).resolve().parents[1]
    shutil.copy2(addon_overlay / "Sources" / "ModelDumpCommands.cpp", addon_source / "Sources" / "ModelDumpCommands.cpp")
    shutil.copy2(addon_overlay / "Sources" / "ModelDumpCommands.hpp", addon_source / "Sources" / "ModelDumpCommands.hpp")
    overlay_registration(addon_source)

    vc, sdk_root, sdk_version, cmake = resolve_toolchain(args)
    env = os.environ.copy()
    env["VSLANG"] = "1033"
    path_additions = [vc / "bin" / "Hostx64" / "x64", sdk_root / "bin" / sdk_version / "x64"]
    env["PATH"] = ";".join(str(p) for p in path_additions) + ";" + env.get("PATH", "")
    env["INCLUDE"] = ";".join(str(p) for p in [vc / "include"] +
        [sdk_root / "Include" / sdk_version / x for x in ("ucrt", "shared", "um", "winrt", "cppwinrt")])
    env["LIB"] = ";".join(str(p) for p in [vc / "lib" / "x64",
        sdk_root / "Lib" / sdk_version / "um" / "x64", sdk_root / "Lib" / sdk_version / "ucrt" / "x64"])
    cmake_args = [str(cmake), "-S", str(addon_source), "-B", str(build_root / "build"),
        "-G", "NMake Makefiles", "-DCMAKE_BUILD_TYPE=Release", "-DAC_VERSION=29",
        "-DAC_API_DEVKIT_DIR=" + str(Path(args.devkit).resolve())]
    subprocess.run(cmake_args, env=env, check=True)
    subprocess.run([str(cmake), "--build", str(build_root / "build")], env=env, check=True)
    print(f"Build passed. Overlay sources: {addon_source}; build output: {build_root / 'build'}")


if __name__ == "__main__":
    main()
