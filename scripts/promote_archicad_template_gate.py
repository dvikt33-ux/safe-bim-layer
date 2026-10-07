"""Promote proven Archicad live gates into template registries.

This helper never talks to Archicad. It consumes the JSON evidence produced by
live smoke/calibration stages and changes only the single registry flag that
the corresponding production stage requires.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "archicad-template"
CALIBRATION = SPEC / "master-layout-coordinate-calibration-v0.1.yaml"
AUTOTEXT = SPEC / "autotext-titleblock-registry-v0.1.yaml"


def load_result(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Evidence JSON root must be an object.")
    if data.get("status") != "PASS":
        raise SystemExit(f"Evidence status must be PASS, got {data.get('status')!r}.")
    return data


def replace_exact_line(path: Path, prefix: str, new_line: str):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise SystemExit(
            f"{path}: expected exactly one line starting with {prefix!r}, "
            f"found {len(matches)}."
        )
    lines[matches[0]] = new_line
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def promote_coordinate(evidence: Path):
    data = load_result(evidence)
    convention = data.get("confirmedConvention")
    cleanup = data.get("cleanup") or {}
    if convention not in {"H1", "H2"}:
        raise SystemExit(
            "Coordinate evidence must contain confirmedConvention H1 or H2."
        )
    if not cleanup.get("success"):
        raise SystemExit("Coordinate evidence cleanup.success must be true.")
    if not cleanup.get("modelElementCountUnchanged"):
        raise SystemExit(
            "Coordinate evidence must prove modelElementCountUnchanged=true."
        )

    current = CALIBRATION.read_text(encoding="utf-8")
    expected_line = f"confirmed_convention: {convention}"
    if expected_line in current:
        return {
            "status": "PASS",
            "changed": False,
            "registry": str(CALIBRATION),
            "confirmedConvention": convention,
        }
    for other in ("H1", "H2"):
        other_line = f"confirmed_convention: {other}"
        if other != convention and other_line in current:
            raise SystemExit(
                f"Registry already contains conflicting {other_line!r}; "
                "refusing automatic replacement."
            )

    replace_exact_line(
        CALIBRATION,
        "confirmed_convention:",
        expected_line,
    )
    return {
        "status": "PASS",
        "changed": True,
        "registry": str(CALIBRATION),
        "confirmedConvention": convention,
        "evidence": str(evidence),
    }


def promote_master_context(evidence: Path):
    data = load_result(evidence)
    cleanup = data.get("cleanup") or {}
    if data.get("masterContextAutoTextVerified") is not True:
        raise SystemExit(
            "Master-context evidence must contain "
            "masterContextAutoTextVerified=true."
        )
    required_cleanup = {
        "success": True,
        "layoutDeleted": True,
        "subsetDeleted": True,
        "contextCleared": True,
        "modelElementCountUnchanged": True,
    }
    bad = {
        key: cleanup.get(key)
        for key, expected in required_cleanup.items()
        if cleanup.get(key) is not expected
    }
    if bad:
        raise SystemExit(
            f"Master-context cleanup proof is incomplete or false: {bad}"
        )

    current = AUTOTEXT.read_text(encoding="utf-8")
    if "production_master_context_verified: true" in current:
        return {
            "status": "PASS",
            "changed": False,
            "registry": str(AUTOTEXT),
            "productionMasterContextVerified": True,
        }
    replace_exact_line(
        AUTOTEXT,
        "production_master_context_verified:",
        "production_master_context_verified: true",
    )
    return {
        "status": "PASS",
        "changed": True,
        "registry": str(AUTOTEXT),
        "productionMasterContextVerified": True,
        "evidence": str(evidence),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "gate",
        choices=("coordinate", "master-context-autotext"),
    )
    parser.add_argument(
        "--evidence",
        required=True,
        type=Path,
        help="JSON result emitted by the corresponding live gate.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional JSON summary path.",
    )
    args = parser.parse_args()

    if not args.evidence.is_file():
        raise SystemExit(f"Evidence file not found: {args.evidence}")

    if args.gate == "coordinate":
        result = promote_coordinate(args.evidence)
    else:
        result = promote_master_context(args.evidence)

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
