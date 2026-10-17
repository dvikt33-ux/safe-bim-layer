"""Explicit Windows-only isolated installer for APA read-only IFC/PDF/DXF tools.

Never installs into the host interpreter or overwrites stable scripts, .apx,
PLN, SceneWriter SQLite, the AI Dispatcher or its background receiver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
DEST = ROOT / "external-tools" / "apa-readonly-v1"
SOURCE_DIR = Path(__file__).resolve().parent
ADAPTER = SOURCE_DIR / "apa_external_readonly.py"
CATALOG = SOURCE_DIR / "apa_external_catalog.py"
REQUIREMENTS = SOURCE_DIR / "requirements-external-readonly.txt"


def require(ok, code):
    if not ok:
        raise ValueError(code)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def installed_python():
    return DEST / "venv" / "Scripts" / "python.exe"


def check():
    manifest = DEST / "installation.json"
    require(manifest.is_file(), "EXTERNAL_TOOLS_NOT_INSTALLED")
    m = json.loads(manifest.read_text(encoding="utf-8"))
    require(m.get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1",
            "INSTALL_MANIFEST_INVALID")
    a = DEST / "apa_external_readonly.py"
    catalog = DEST / "apa_external_catalog.py"
    r = DEST / "requirements-external-readonly.txt"
    require(a.is_file() and catalog.is_file()
            and digest(catalog) == m["catalogSHA256"] and r.is_file()
            and digest(a) == m["adapterSHA256"]
            and digest(r) == m["requirementsSHA256"],
            "INSTALLED_ADAPTER_DRIFT")
    py = installed_python()
    require(py.is_file(), "ISOLATED_PYTHON_NOT_FOUND")
    result = subprocess.run([str(py), str(a), "doctor"], timeout=45,
                            capture_output=True, text=True)
    require(result.returncode == 0, "ISOLATED_DOCTOR_NOT_READY:"
            + (result.stdout + result.stderr)[-1000:])
    return {"status": "EXTERNAL_READONLY_INSTALLED_READY",
            "root": str(DEST), "python": str(py),
            "adapter": str(a), "modelWrites": 0,
            "archicadNativeCalls": 0}


def install():
    require(sys.platform == "win32" and platform.machine().lower() in
            {"amd64", "x86_64"}, "WINDOWS_X64_REQUIRED")
    require(sys.version_info[:2] in {(3, 11), (3, 12)}, "INSTALL_USING_PYTHON_3_11_OR_3_12_REQUIRED")
    require(ROOT.is_dir() and (ROOT / "scripts" /
            "archicad_project_accelerator.py").is_file()
            and (ROOT / "scripts" /
            "archicad_connected_ifc.py").is_file(),
            "EXISTING_STABLE_APA_INSTALL_NOT_FOUND")
    require(ADAPTER.is_file() and CATALOG.is_file() and REQUIREMENTS.is_file(),
            "SOURCE_CHECKOUT_MISSING_INSTALL_FILES")
    require(not DEST.exists(),
            "EXTERNAL_READONLY_TARGET_ALREADY_EXISTS_RUN_CHECK_OR_AUDIT")
    require((ROOT / "apa-selector-install-receipt.json").is_file(),
            "STABLE_APA_INSTALL_RECEIPT_MISSING")
    require((ROOT / "external-tools").exists() is False
            or (ROOT / "external-tools").is_dir(),
            "EXTERNAL_TOOLS_PATH_NOT_DIRECTORY")
    # This is the ONLY local destination. In case of a failed pip install,
    # retain the partial directory for inspection and refuse a blind replay.
    DEST.mkdir(parents=True, exist_ok=False)
    import shutil
    shutil.copyfile(ADAPTER, DEST / ADAPTER.name)
    shutil.copyfile(CATALOG, DEST / CATALOG.name)
    shutil.copyfile(REQUIREMENTS, DEST / REQUIREMENTS.name)
    venv.EnvBuilder(with_pip=True, clear=False,
                    symlinks=False).create(str(DEST / "venv"))
    py = installed_python()
    require(py.is_file(), "VENV_CREATION_FAILED")
    env = dict(os.environ)
    env["PIP_REQUIRE_VIRTUALENV"] = "true"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    # IfcTester needs odfpy 1.4.1; PyPI publishes only a source tarball.
    # Verify the exact official PyPI SHA-256 before running its build.
    vendor_dir = DEST / "verified-upstream-src"
    vendor_dir.mkdir(exist_ok=False)
    subprocess.run([str(py), "-m", "pip", "download", "--no-deps",
                    "--no-binary=:all:", "--no-input",
                    "--dest", str(vendor_dir), "odfpy==1.4.1"],
                   env=env, check=True, timeout=300)
    source_tar = vendor_dir / "odfpy-1.4.1.tar.gz"
    require(source_tar.is_file() and
            digest(source_tar) ==
            "db766a6e59c5103212f3cc92ec8dd50a0f3a02790233ed0b52148b70d3c438ec",
            "ODFPY_PYPI_SOURCE_SHA256_MISMATCH")
    subprocess.run([str(py), "-m", "pip", "install", "--no-input",
                    "--no-deps", str(source_tar)],
                   env=env, check=True, timeout=300)
    subprocess.run([str(py), "-m", "pip", "install", "--no-input",
                    "--only-binary=:all:", "-r", str(DEST / REQUIREMENTS.name)],
                   env=env, check=True, timeout=2400)
    subprocess.run([str(py), "-m", "pip", "check"], env=env,
                   check=True, timeout=120)
    require(subprocess.run(
        [str(py), str(DEST / ADAPTER.name), "doctor"],
        capture_output=True, timeout=120).returncode == 0,
        "PINNED_PACKAGES_DOCTOR_FAILED")
    for module in ("ifcdiff", "ifcclash", "ifctester"):
        check_cli = subprocess.run(
            [str(py), "-m", module, "--help"],
            capture_output=True, timeout=90)
        require(check_cli.returncode == 0, "VENDOR_CLI_IMPORT_FAILED:" + module)
    receipt = {"schema": "APA_EXTERNAL_READONLY_INSTALL_V1",
               "status": "EXTERNAL_READONLY_INSTALLED_READY",
               "adapterSHA256": digest(DEST / ADAPTER.name),
               "catalogSHA256": digest(DEST / CATALOG.name),
               "requirementsSHA256": digest(DEST / REQUIREMENTS.name),
               "python": str(py), "scriptsModified": False,
               "coreModified": False, "addonsModified": False,
               "plnModified": False, "dispatcherModified": False,
               "modelWrites": 0, "nativeCalls": 0}
    with (DEST / "installation.json").open("x", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return check()


def main(argv=None):
    p = argparse.ArgumentParser(description="APA AC29 external tools isolated installer")
    p.add_argument("--install", action="store_true",
                   help="explicitly create and pip-install a separate Python 3.11/3.12 venv")
    p.add_argument("--check", action="store_true",
                   help="verify existing isolated install without mutations")
    args = p.parse_args(argv)
    require(not (args.install and args.check), "CHOOSE_ONE_ACTION")
    result = install() if args.install else check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_STATUS: EXTERNAL_READONLY_INSTALL_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
