"""One-time opt-in, isolated APA Semantic bridge install on Windows.

Only creates C:\LocalAI\APA_AC29_Stable\external-tools\apa-semantic-v1.
Never patches, overwrites, or restarts the existing APA 29/6-vendor stack.
PyMuPDF installed in its OWN venv. Model weights are NOT downloaded.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import venv

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
OLD = ROOT / "external-tools" / "apa-readonly-v1"
DEST = ROOT / "external-tools" / "apa-semantic-v1"
HERE = Path(__file__).resolve().parent
NAMES = ("apa_semantic_readonly.py", "apa_semantic_catalog.py",
         "apa_semantic_entrypoint.py")
PIN = "1.26.4"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_original():
    base = OLD / "installation.json"
    factory = OLD / "session-factory-v1" / "session-factory-install.json"
    require(base.is_file() and factory.is_file(),
            "SIX_VENDOR_FACTORY_NOT_INSTALLED")
    a = json.loads(base.read_text(encoding="utf-8"))
    f = json.loads(factory.read_text(encoding="utf-8"))
    require(a.get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1"
            and f.get("schema") == "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1",
            "ORIGINAL_RECEIPTS_INVALID")
    for path, key in [
        (OLD / "apa_external_readonly.py", "adapterSHA256"),
        (OLD / "apa_external_catalog.py", "catalogSHA256"),
    ]:
        require(path.is_file() and sha(path) == a.get(key) == f.get(key),
                "ORIGINAL_PINNED_SIDECAR_DRIFT:" + key)
    require((OLD / "session-factory-v1"
             / "apa_external_analytics_entrypoint.py").is_file(),
            "ORIGINAL_ROUTED_ANALYTICS_ENTRYPOINT_MISSING")
    return a, f


def review():
    require(sys.platform == "win32" and
            platform.machine().lower() in {"amd64", "x86_64"}
            and sys.version_info[:2] in {(3, 11), (3, 12)},
            "WINDOWS_PYTHON_3_11_OR_3_12_REQUIRED")
    checked_original()
    require(all((HERE / name).is_file() for name in NAMES),
            "SEMANTIC_SOURCE_FILES_MISSING")
    require(not DEST.exists(), "SEMANTIC_INSTALL_EXISTS_USE_CHECK")
    require(DEST.parent.is_dir(), "STABLE_EXTERNAL_TOOLS_PARENT_MISSING")
    for name in NAMES:
        compile((HERE / name).read_bytes(), str(HERE / name), "exec")
    return {"status": "SEMANTIC_INSTALL_PREFLIGHT_READY",
            "destination": str(DEST), "willModifyOriginalAPA": False,
            "modelWeightsDownloaded": False}


def check():
    checked_original()
    manifest_path = DEST / "installation.json"
    py = DEST / "venv" / "Scripts" / "python.exe"
    require(manifest_path.is_file() and py.is_file(),
            "SEMANTIC_INSTALL_RECEIPT_OR_VENV_MISSING")
    receipt = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(receipt.get("schema") == "APA_SEMANTIC_BRIDGE_INSTALL_V1"
            and receipt.get("pymupdfVersion") == PIN
            and receipt.get("workerSHA256")
                == sha(DEST / "apa_semantic_readonly.py")
            and receipt.get("catalogSHA256")
                == sha(DEST / "apa_semantic_catalog.py")
            and receipt.get("entrypointSHA256")
                == sha(DEST / "apa_semantic_entrypoint.py"),
            "SEMANTIC_INSTALL_SOURCE_SHA_DRIFT")
    ver = subprocess.run(
        [str(py), "-c", "import importlib.metadata; print(importlib.metadata.version('pymupdf'))"],
        capture_output=True, text=True, timeout=60)
    require(ver.returncode == 0 and ver.stdout.strip() == PIN,
            "PINNED_PYMUPDF_VERSION_DRIFT")
    probe = subprocess.run([str(py),
                            str(DEST / "apa_semantic_entrypoint.py"),
                            "--probe"], capture_output=True, text=True, timeout=120)
    require(probe.returncode == 0,
            "ORIGINAL_ROUTER_OR_NEW_SEMANTIC_PROVIDER_BLOCKED:"
            + probe.stdout[-700:] + probe.stderr[-700:])
    result = json.loads(probe.stdout)
    require(result["status"] == "APA_SEMANTIC_ROUTER_REGISTERED"
            and len(result["semanticCommands"]) == 4
            and result["originalSixCommandsPreserved"] is True
            and result["nativeCalls"] == result["modelWrites"] == 0,
            "SEMANTIC_ROUTER_PROBE_FAILED")
    return {"status": "APA_SEMANTIC_INSTALLED_AND_ROUTER_REGISTERED",
            "commands": result["semanticCommands"],
            "originalSixPreserved": True, "modelInferenceVerified": False,
            "modelWeightsInstalled": (DEST / "models.json").is_file(),
            "nativeCalls": 0, "plnWrites": 0}


def install():
    review()
    # Never overwrite anything; partial installs are inspect-only.
    DEST.mkdir(exist_ok=False)
    for name in NAMES:
        shutil.copyfile(HERE / name, DEST / name)
    venv.EnvBuilder(with_pip=True, symlinks=False).create(str(DEST / "venv"))
    py = DEST / "venv" / "Scripts" / "python.exe"
    require(py.is_file(), "SEMANTIC_VENV_FAILED")
    pip = subprocess.run(
        [str(py), "-m", "pip", "install", "--disable-pip-version-check",
         "--only-binary=:all:", "pymupdf==" + PIN],
        capture_output=True, text=True, timeout=900)
    require(pip.returncode == 0,
            "PINNED_PYMUPDF_INSTALL_FAILED:" + pip.stderr[-650:])
    receipt = {"schema": "APA_SEMANTIC_BRIDGE_INSTALL_V1",
               "pymupdfVersion": PIN,
               "workerSHA256": sha(DEST / "apa_semantic_readonly.py"),
               "catalogSHA256": sha(DEST / "apa_semantic_catalog.py"),
               "entrypointSHA256": sha(DEST / "apa_semantic_entrypoint.py"),
               "existingSixVendorChanges": 0,
               "modelWeightsDownloaded": False,
               "plnWrites": 0, "nativeCalls": 0}
    with (DEST / "installation.json").open("x", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return check()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--install", action="store_true")
    g.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    r = install() if args.install else check() if args.check else review()
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("SEMANTIC_INSTALL_BLOCKED:" + type(exc).__name__ + ":"
              + str(exc), file=sys.stderr)
        sys.exit(2)
