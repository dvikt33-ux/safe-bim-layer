"""Consume the ALREADY successful BDD House native wall-read report.

No Archicad connections, APA modifications, or native command calls.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import base64
import subprocess

REPORT_REPO = "dvikt33-ux/safe-bim-bridge"
REPORT_PATH = "safe-bim-mailbox/gpt-live/results/apa-bdd-selected-tapir-20261017-133000.json"
TASK_REPO = "dvikt33-ux/safe-bim-layer"
TASK_PATH = "examples/accelerator/bdd-house-20261017-auto-selector-source-read.json"
TASK_REF = "7a8b88275172da3b866648bc6f580ba762fb7f6a"
REPORT_BLOB = "b8961f6b69dc2cc074de0e69474ee79a4ae56a21"
TASK_BLOB = "a77b3a45b0020c4274f8d11bf33c6c0ccd309e86"


def read_pinned_json(repo, path, ref, expected_blob):
    # Authenticated access via the user's existing gh login. GitHub private
    # repos deliberately return HTTP 404 to unauthenticated raw URLs.
    raw = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}"],
        stderr=subprocess.PIPE, timeout=45
    )
    response = json.loads(raw.decode("utf-8"))
    data = base64.b64decode(response["content"])
    sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if sha != expected_blob or response.get("sha") != expected_blob:
        raise ValueError("GITHUB_EVIDENCE_CHANGED")
    return json.loads(data.decode("utf-8-sig"))


def require(ok, error):
    if not ok:
        raise ValueError(error)


def main():
    try:
        report = read_pinned_json(REPORT_REPO, REPORT_PATH, "main", REPORT_BLOB)
        task = read_pinned_json(TASK_REPO, TASK_PATH, TASK_REF, TASK_BLOB)
        steps = task["steps"]
        require(task["schemaVersion"] == "apa-capability-task/1" and len(steps) == 2,
                "SOURCE_TASK_CHANGED")
        ids = []
        for step in steps:
            proof = step["sourceVerification"]
            record = {k: v for k, v in step.items() if k != "sourceVerification"}
            computed = hashlib.sha256(json.dumps(
                record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")).hexdigest()
            require(step["effect"] == step["impact"] == "READ_ONLY"
                    and computed == proof["dataHash"], "SOURCE_TASK_HASH_CHANGED")
            ids.append([x["elementId"]["guid"].lower()
                        for x in step["parameters"]["elements"]])
        require(ids[0] == ids[1] and len(set(ids[0])) == 6,
                "SIX_WALL_SOURCES_NOT_VERIFIED")
        require(report["status"] == "LIVE_AUTO_SELECTOR_TAPIR_READ_PASS"
                and report["selectedCommands"] ==
                ["GetDetailsOfElements", "Get3DBoundingBoxes"]
                and report["guidCount"] == report["finalGUIDCount"] == 290
                and report["nativeWriteAttempts"] == 0
                and report["writeRequested"] is False, "NATIVE_READ_PASS_NOT_VERIFIED")
        details, boxes = report["wallDetails"], report["wallBoundingBoxes"]
        require(len(details) == len(boxes) == 6, "SIX_WALL_RESULTS_NOT_FOUND")
        pln = Path(report["project"]["path"])
        require(pln.is_file(), "BDD_WORKING_PLN_NOT_FOUND")
        local_hash = hashlib.sha256(pln.read_bytes()).hexdigest()
        require(local_hash == report["workingSHA256"],
                "SAVED_PLN_CHANGED_SINCE_READ_REVALIDATION_REQUIRED")
        wall_rows = []
        for i, (row, box) in enumerate(zip(details, boxes), 1):
            d = row["details"]
            require(row["type"] == "Wall"
                    and d["geometryType"] == "Straight"
                    and isinstance(box["boundingBox3D"], dict),
                    "NATIVE_WALL_GEOMETRY_INCOMPLETE")
            wall_rows.append({
                "nativeOutputIndex": i,
                "nativeLabel": row.get("id"),
                "beginXY": d["begCoordinate"],
                "endXY": d["endCoordinate"],
                "height": d["height"],
                "thickness": [d["begThickness"], d["endThickness"]],
                "z": d["zCoordinate"],
                "boundingBox3D": box["boundingBox3D"],
                "rawDetails": row,
            })
        package = {
            "schema": "APA_BDD_EXISTING_WALL_EVIDENCE_V1",
            "status": "PREVIOUS_NATIVE_PASS_REUSED",
            "sourceReport": f"https://github.com/{REPORT_REPO}/blob/main/{REPORT_PATH}",
            "sourceTask": f"https://github.com/{TASK_REPO}/blob/{TASK_REF}/{TASK_PATH}",
            "sourceHostGuids": ids[0],
            "guidToOutputRowAssociation": "NOT_INDEPENDENTLY_VERIFIED",
            "walls": wall_rows,
            "savedPLNSHA256": local_hash,
            "savedPLNMatchesPriorReport": True,
            "unsavedLiveModelState": "NOT_RECHECKED",
            "nativeCalls": 0,
            "modelWrites": 0,
            "writeAuthorization": False,
            "next": "Source-verify KR-10 to KR-15 interior frame placements before any model writes",
        }
        filename = "bdd-source-wall-evidence-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        output = Path(tempfile.gettempdir()) / filename
        with output.open("x", encoding="utf-8") as handle:
            json.dump(package, handle, ensure_ascii=False, indent=2)
        print("APA_STATUS: EXISTING_NATIVE_PASS_REUSED")
        print("WALLS: 6 | GUIDS: 290 | NATIVE_CALLS: 0 | MODEL_WRITES: 0")
        for row in wall_rows:
            a, b = row["beginXY"], row["endXY"]
            print(f"WALL_{row['nativeOutputIndex']}: ({a['x']:.3f},{a['y']:.3f})"
                  f" -> ({b['x']:.3f},{b['y']:.3f})")
        print("PACKAGE:", output)
        print("NEXT: 2022 KR internal-frame source dimensions; no model writes")
        return 0
    except Exception as error:
        print("APA_STATUS: BLOCKED_NO_CHANGES")
        print("ERROR:", type(error).__name__ + ":", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
