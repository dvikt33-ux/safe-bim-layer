"""Explicit opt-in trusted model registration for the APA semantic bridge.

Downloads nothing, installs nothing, imports no vendor code, runs no weights.
Vendor models are untrusted executable pickle (.pt/.pth) in upstream code:
the operator MUST verify publisher/source and pass --trust-checkpoint.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

SIDE = Path(r"C:\LocalAI\APA_AC29_Stable\external-tools\apa-semantic-v1")
TARGET = SIDE / "models.json"
SCHEMA = "APA_SEMANTIC_ML_VENDOR_CONFIG_V1"
VENDORS = ("openbim", "raster2seq")


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(p):
    digest = hashlib.sha256()
    with p.open("rb") as fd:
        for block in iter(lambda: fd.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify():
    require(TARGET.is_file(), "NO_ML_MODELS_CONFIGURED")
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    require(data.get("schema") == SCHEMA, "ML_CONFIG_INVALID")
    present = []
    for vendor in VENDORS:
        if vendor not in data:
            continue
        item = data[vendor]
        exe = Path(item["python"]).resolve(strict=True)
        root = Path(item["root"]).resolve(strict=True)
        model = Path(item["model"]).resolve(strict=True)
        require(exe.is_file() and root.is_dir() and model.is_file()
                and sha(model) == item["modelSHA256"],
                "MODEL_SHA_OR_PATH_DRIFT:" + vendor)
        present.append(vendor)
    return {"status": "MODEL_PATHS_VERIFIED_NOT_INFERENCE_TESTED",
            "configured": present,
            "downloads": 0, "plnWrites": 0, "nativeCalls": 0}


def configure(vendor, python, root, model, trust):
    require(trust, "UNTRUSTED_PICKLE_MODEL_REQUIRES_EXPLICIT_TRUST")
    require(vendor in VENDORS, "UNKNOWN_ML_VENDOR")
    require(SIDE.is_dir()
            and (SIDE / "installation.json").is_file(),
            "SEMANTIC_BRIDGE_NOT_INSTALLED")
    exe, rootpath, weight = (
        Path(p).resolve(strict=True) for p in (python, root, model))
    require(exe.is_file() and rootpath.is_dir() and weight.is_file(),
            "MODEL_OR_VENDOR_PATH_NOT_FOUND")
    if vendor == "openbim":
        require((rootpath / "inference_api.py").is_file()
                and weight.suffix.lower() == ".pt",
                "OPENBIM_VENDOR_SCRIPT_OR_PT_MISSING")
    else:
        require((rootpath / "scripts" / "parse_floorplan.py").is_file()
                and weight.name == "checkpoint.pth"
                and weight.parent.name == "cubicasa5k"
                and weight.parent.parent.name == "raster2seq",
                "RASTER2SEQ_VENDOR_SCRIPT_OR_CKPT_LAYOUT_MISSING")
    value = {"python": str(exe), "root": str(rootpath),
             "model": str(weight), "modelSHA256": sha(weight)}
    if TARGET.exists():
        existing = json.loads(TARGET.read_text(encoding="utf-8"))
        require(existing.get("schema") == SCHEMA,
                "PREVIOUS_ML_CONFIG_NOT_OWNED")
        require(vendor not in existing,
                "VENDOR_CONFIG_ALREADY_EXISTS_DO_NOT_REPLACE")
        backup = TARGET.with_name("models-" + sha(TARGET)[:16] + ".json.backup")
        require(not backup.exists(), "MODEL_CONFIG_BACKUP_EXISTS_AUDIT")
        with backup.open("xb") as fd:
            fd.write(TARGET.read_bytes())
    else:
        existing = {"schema": SCHEMA}
    existing[vendor] = value
    staged = TARGET.with_name("models.json.next")
    require(not staged.exists(), "MODEL_CONFIG_STAGING_CONFLICT")
    with staged.open("x", encoding="utf-8") as fd:
        json.dump(existing, fd, ensure_ascii=False, indent=2)
        fd.write("\n")
    os.replace(staged, TARGET)
    return verify()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true")
    p.add_argument("--vendor", choices=VENDORS)
    p.add_argument("--python")
    p.add_argument("--root")
    p.add_argument("--model")
    p.add_argument("--trust-checkpoint", action="store_true")
    args = p.parse_args(argv)
    if args.verify:
        result = verify()
    else:
        require(all((args.vendor, args.python, args.root, args.model)),
                "COMPLETE_MODEL_CONFIG_REQUIRED")
        result = configure(args.vendor, args.python, args.root, args.model,
                           args.trust_checkpoint)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ML_MODEL_CONFIG_BLOCKED:" + type(e).__name__ + ":" + str(e),
              file=sys.stderr)
        sys.exit(2)
