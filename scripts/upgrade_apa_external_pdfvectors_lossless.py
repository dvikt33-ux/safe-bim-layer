"""One-shot isolated upgrade: lossless PDFVectors only, no core/PLN writes.

Fails if bytes differ outside original PDFVectors function. Updates BOTH
installed adapter-SHA receipts (base and session-factory), preserving
six-command original router registrations. Default is read-only preflight.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
FOLDER = ROOT / "external-tools" / "apa-readonly-v1"
SESSION = FOLDER / "session-factory-v1"
SOURCE = Path(__file__).resolve().with_name("apa_external_readonly.py")
DEST = FOLDER / "apa_external_readonly.py"
RECEIPTS = (
    FOLDER / "installation.json",
    SESSION / "session-factory-install.json",
)
BACKUP = FOLDER / "upgrade-pdfvectors-lossless-v1"


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def review():
    require(SOURCE.is_file() and DEST.is_file()
            and all(p.is_file() for p in RECEIPTS)
            and (FOLDER / "venv" / "Scripts" / "python.exe").is_file(),
            "PDF_UPGRADE_SOURCE_OR_INSTALLED_SIDECAR_MISSING")
    old_bytes = DEST.read_bytes()
    new_bytes = SOURCE.read_bytes()
    old = old_bytes.decode("utf-8").replace("\r\n", "\n")
    new = new_bytes.decode("utf-8").replace("\r\n", "\n")
    old_marker, new_marker, tail = (
        "def pdf_vectors(args):",
        "def _pdf_path_ops(path, height):",
        "def dxf_vectors(args):",
    )
    require(old.count(old_marker) == 1
            and old.count(new_marker) == 0
            and new.count(old_marker) == 1
            and new.count(new_marker) == 1
            and old.count(tail) == new.count(tail) == 1,
            "EXPECTED_OLD_PDF_ONLY_AND_NEW_VECTOR_PATCH_REQUIRED")
    before_old, after_old = old.split(old_marker, 1)
    before_new, after_new = new.split(new_marker, 1)
    require(before_old == before_new
            and after_old.split(tail, 1)[1] == after_new.split(tail, 1)[1],
            "PDF_PATCH_ALTERS_NON_PDF_ADAPTER_CODE")
    compile(new_bytes, str(SOURCE), "exec")
    receipts = [json.loads(p.read_text(encoding="utf-8")) for p in RECEIPTS]
    require(receipts[0].get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1"
            and receipts[1].get("schema")
                == "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1"
            and all(r.get("adapterSHA256") == sha(old_bytes)
                    for r in receipts),
            "CURRENT_INSTALL_AND_FACTORY_ADAPTER_HASH_MISMATCH")
    catalog = FOLDER / "apa_external_catalog.py"
    require(catalog.is_file()
            and all(r.get("catalogSHA256") == sha(catalog.read_bytes())
                    for r in receipts),
            "CURRENT_CATALOG_SHA_DRIFT")
    require(not BACKUP.exists(), "PDF_UPGRADE_ALREADY_RESERVED_OR_ATTEMPTED")
    require(sha(new_bytes) != sha(old_bytes), "NEW_ADAPTER_ALREADY_INSTALLED")
    return {"old": old_bytes, "new": new_bytes,
            "receipts": [p.read_bytes() for p in RECEIPTS],
            "records": receipts}


def upgrade():
    state = review()
    BACKUP.mkdir(parents=False, exist_ok=False)
    (BACKUP / "apa_external_readonly.py.original").write_bytes(state["old"])
    for path, content in zip(RECEIPTS, state["receipts"]):
        (BACKUP / (path.parent.name + "-" + path.name + ".original")).write_bytes(content)
    new_sha = sha(state["new"])
    new_records = []
    for record in state["records"]:
        updated = dict(record)
        updated["adapterSHA256"] = new_sha
        updated["pdfVectorsLosslessUpgrade"] = {
            "status": "APPLIED",
            "oldAdapterSHA256": sha(state["old"]),
            "newAdapterSHA256": new_sha,
            "modelWrites": 0, "nativeCalls": 0,
        }
        new_records.append(updated)
    staging = [(DEST.with_name(DEST.name + ".pdfv-next"), state["new"])]
    for path, record in zip(RECEIPTS, new_records):
        staging.append((path.with_name(path.name + ".pdfv-next"),
                        (json.dumps(record, ensure_ascii=False, indent=2)
                         + "\n").encode("utf-8")))
    try:
        require(all(not p.exists() for p, _ in staging),
                "PDF_UPGRADE_STAGING_CONFLICT")
        for path, data in staging:
            with path.open("xb") as fd:
                fd.write(data)
        for (staged, _), dest in zip(staging, (DEST, *RECEIPTS)):
            os.replace(staged, dest)
        py = FOLDER / "venv" / "Scripts" / "python.exe"
        result = subprocess.run(
            [str(py), str(DEST), "doctor"],
            capture_output=True, text=True, timeout=120)
        require(result.returncode == 0, "UPGRADED_ADAPTER_DOCTOR_BLOCKED:"
                + result.stdout[-500:] + result.stderr[-500:])
        require(sha(DEST.read_bytes()) == new_sha
                and all(json.loads(p.read_text(encoding="utf-8"))
                        ["adapterSHA256"] == new_sha for p in RECEIPTS),
                "UPGRADE_SHA_READBACK_FAILED")
    except BaseException:
        for target, blob in zip((DEST, *RECEIPTS),
                                (state["old"], *state["receipts"])):
            staged = target.with_name(target.name + ".pdfv-rollback")
            staged.write_bytes(blob)
            os.replace(staged, target)
        raise
    finally:
        for staged, _ in staging:
            if staged.exists():
                staged.unlink()
    return {"status": "PDF_VECTORS_LOSSLESS_INSTALLED",
            "adapterSHA256": new_sha, "backup": str(BACKUP),
            "baseAndFactoryReceiptsUpdated": True,
            "coreChanged": False, "modelWrites": 0, "nativeCalls": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    result = upgrade() if args.apply else review()
    if not args.apply:
        result = {"status": "PDF_UPGRADE_PREFLIGHT_READ_ONLY_PASS",
                  "fromSHA256": sha(result["old"]),
                  "toSHA256": sha(result["new"]),
                  "modelWrites": 0, "nativeCalls": 0}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PDF_VECTORS_UPGRADE_BLOCKED: " + type(exc).__name__
              + ": " + str(exc), file=sys.stderr)
        raise SystemExit(2)
