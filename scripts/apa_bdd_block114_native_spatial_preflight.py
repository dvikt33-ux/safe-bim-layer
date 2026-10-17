"""BDD 2022 block 1.14 spatial production preflight, READ ONLY.

Checks all seven vector-calibrated candidate studs against CURRENT AC29 native
BREP body bounding boxes, logs actual roof/wall junction candidates. No
Create/Modify/Copy/Save command is allowed or dispatched.
"""
from __future__ import annotations
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable\scripts")
WORKING = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
ORIGINAL = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
SAVED_SHA = "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
ORIGINAL_SHA = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
CORE_SHA = "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b"
DYNAMIC_SHA = "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8"
SELECTOR_SHA = "32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce"
PROTOTYPE = "b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
NORTH_WALL = "7b332594-ab82-43b4-bfc2-ab5ad549c2c9"
CANDIDATES_REPO = "dvikt33-ux/safe-bim-layer"
CANDIDATES_REF = "27ab165bbe21430a071dac47509c94590630de0a"
CANDIDATES_FILE = "examples/accelerator/bdd-house-block-114-graphic-vector-calibrated-targets.json"
CANDIDATES_BLOB = "0622119083ad2d5271dc71bb8cf474ba7ef823bc"
REPORT_REPO = "dvikt33-ux/safe-bim-bridge"
TOL = 0.000001


def require(value, problem):
    if not value:
        raise ValueError(problem)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_candidates():
    request = ("repos/" + CANDIDATES_REPO + "/contents/"
               + CANDIDATES_FILE + "?ref=" + CANDIDATES_REF)
    result = subprocess.run(["gh", "api", request],
                            capture_output=True, timeout=45)
    require(result.returncode == 0, "GITHUB_CANDIDATE_RETRIEVAL_FAILED")
    obj = json.loads(result.stdout.decode("utf-8"))
    raw = base64.b64decode(obj["content"])
    checked = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    require(checked == CANDIDATES_BLOB == obj["sha"],
            "SOURCE_CALIBRATION_BLOB_DRIFT")
    return json.loads(raw.decode("utf-8"))


def aabb(vertices):
    if not vertices:
        return None
    if any(not isinstance(v, list) or len(v) != 3 or
           any(type(n) not in (float, int) or not math.isfinite(n) for n in v)
           for v in vertices):
        raise ValueError("NATIVE_BREP_BAD_VERTICES")
    return [(min(v[i] for v in vertices), max(v[i] for v in vertices))
            for i in range(3)]


def touches(a, b, epsilon=TOL):
    # Volumetric AABB intersection (not exact solid intersection).
    return all(a[i][0] < b[i][1]-epsilon and b[i][0] < a[i][1]-epsilon
               for i in range(3))


def classify(row, guid):
    kind = row.get("type", "Unknown")
    if guid == NORTH_WALL:
        return "NORTH_WALL_EXPECTED_JUNCTION_REQUIRE_NATIVE_JOIN_REVIEW"
    if kind == "Roof":
        return "ROOF_BODY_AABB_POSSIBLE_CONTACT_NEEDS_EXACT_ROOF_SLOPE_REVIEW"
    if kind in {"Wall", "Window", "Door", "Column", "ColumnSegment", "Beam",
                "BeamSegment", "Slab", "Shell"}:
        return "EXISTING_PHYSICAL_BIM_ELEMENT_REQUIRES_JUNCTION_OR_CLASH_REVIEW"
    return "UNCLASSIFIED_EXISTING_BIM_ELEMENT_REQUIRES_REVIEW"


def run():
    require(WORKING.is_file() and ORIGINAL.is_file(), "BDD_SAVED_FILES_NOT_FOUND")
    require(sha(WORKING) == SAVED_SHA and sha(ORIGINAL) == ORIGINAL_SHA,
            "BDD_SAVED_BASELINE_OR_PROTECTED_SOURCE_CHANGED")
    for filename, expected in [
        ("archicad_project_accelerator.py", CORE_SHA),
        ("archicad_dynamic_commands.py", DYNAMIC_SHA),
        ("archicad_strategy_discovery.py", SELECTOR_SHA),
    ]:
        require(sha(STABLE / filename) == expected,
                "STABLE_APA_MODULE_CHANGED:" + filename)
    proof = pinned_candidates()
    positions = proof["members"]
    require(proof.get("modelWrites") == 0 and len(positions) == 7 and
            all(abs(p["center"]["x"]-9.370) < 1e-8 for p in positions),
            "BLOCK_114_CANDIDATE_SCOPE_CHANGED")
    require([round(x["center"]["y"], 3) for x in positions] ==
            [9.255, 8.838, 8.420, 8.008, 7.595, 6.995, 6.395],
            "BLOCK_114_VECTOR_Y_CALIBRATION_CHANGED")
    sys.path.insert(0, str(STABLE))
    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_connected_components as C

    RUN.bind_authorized_saved_copy(
        19727, str(WORKING), WORKING.stem, SAVED_SHA,
        "BDD_BLOCK114_SPATIAL_PREFLIGHT_READ_ONLY_20261017"
    )
    folder = Path(tempfile.mkdtemp(prefix="apa-bdd-114-space-"))
    (folder / "raw").mkdir()
    api = APA.EvidenceAPI(APA.native_transport, folder / "raw", execute=False)
    binding = RUN.guarded_project_for_read(api)
    require(APA.archicad29(api).get("buildNumber") == 5101,
            "WRONG_AC29_BUILD")
    before = set(APA.inventory_guids(api))
    require(len(before) == 290 and PROTOTYPE in before,
            "CURRENT_BDD_MODEL_BASELINE_INVALID")
    model = C.G.normalize_dump(api("GetModelDumpV1", {}))
    native = {r["guid"].lower(): r for r in model["elements"]}
    require(set(native) == before, "NATIVE_BREP_AND_INVENTORY_DIFFER")
    bodies = []
    for guid, row in native.items():
        for body in row.get("bodies", []):
            box = aabb(body.get("vertices", []))
            if box is not None:
                bodies.append((guid, row, box))
    require(bool(bodies), "NATIVE_BREP_HAS_NO_SOLIDS")
    per_stud = []
    for record in positions:
        center = record["center"]
        x, y = center["x"], center["y"]
        candidate = [(x-0.05, x+0.05), (y-0.025, y+0.025), (0, 2.9)]
        overlaps = []
        observed = set()
        for guid, row, box in bodies:
            if guid not in observed and touches(candidate, box):
                observed.add(guid)
                overlaps.append({
                    "guid": guid,
                    "type": row.get("type"),
                    "classification": classify(row, guid),
                    "nativeBodyAABB": box,
                })
        per_stud.append({
            "index": record["index"],
            "x": x, "y": y, "z": 0,
            "candidateBounds": candidate,
            "possibleNativeContacts": overlaps,
            "physicalConclusion": "AABB_IS_CONSERVATIVE_NOT_SOLID_CLASH_PROOF",
        })
    after = set(APA.inventory_guids(api))
    require(after == before and api.write_attempts == 0,
            "MODEL_INVENTORY_CHANGED_OR_WRITE_ATTEMPTED")
    require(sha(WORKING) == SAVED_SHA and sha(ORIGINAL) == ORIGINAL_SHA,
            "SAVED_PLN_CHANGED_DURING_SPATIAL_PREFLIGHT")
    contacts = [row for member in per_stud
                for row in member["possibleNativeContacts"]]
    report = {
        "schema": "APA_BDD_BLOCK114_NATIVE_SPATIAL_PREFLIGHT_V1",
        "status": (
            "NATIVE_SPATIAL_CANDIDATES_REQUIRE_JUNCTION_REVIEW"
            if contacts else "NATIVE_SPATIAL_AABB_CLEAR_FINAL_SOURCE_CHECK_REQUIRED"
        ),
        "selectedExistingCopyPrototype": PROTOTYPE,
        "sourceVectorEvidenceSHA1": CANDIDATES_BLOB,
        "currentPlnGuids": len(after),
        "currentNativeBodyCount": len(bodies),
        "sourceProject": binding["path"],
        "members": per_stud,
        "contactCount": len(contacts),
        "contactsRequireExactGeometryNotJustAABB": bool(contacts),
        "absoluteXIsCalibratedNotPrintedDimension": True,
        "candidateWriteAuthorized": False,
        "modelWrites": api.write_attempts,
        "saveProject": False,
        "next": (
            "Confirm exact top stud junction against current native roof/wall "
            "and approve measured X before guarded seven-column APA SceneWriter batch"
        ),
    }
    output = folder / "block114-spatial.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print("APA_STATUS:", report["status"])
    print("GUIDS:", len(after), "CANDIDATE_STUDS:", len(per_stud),
          "POSSIBLE_AABB_CONTACTS:", len(contacts))
    for item in per_stud:
        brief = [(c["type"], c["classification"].split("_")[0])
                 for c in item["possibleNativeContacts"]]
        print("STUD", item["index"], "(X,Y)=", (item["x"], item["y"]), "CONTACTS:", brief)
    print("MODEL_WRITES:", api.write_attempts)
    print("REPORT:", output)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remote = ("safe-bim-mailbox/gpt-live/results/apa-bdd-114-spatial-"
              + stamp + "-" + uuid4().hex[:8] + ".json")
    upload = folder / "publish.json"
    upload.write_text(json.dumps({
        "branch": "main",
        "message": "BDD 1.14 production spatial preflight from vector-calibrated PDF and real native BREP",
        "content": base64.b64encode(output.read_bytes()).decode("ascii"),
    }), encoding="utf-8")
    result = subprocess.run(
        ["gh", "api", "--method", "PUT",
         f"repos/{REPORT_REPO}/contents/{remote}",
         "--input", str(upload), "--jq", ".content.html_url"],
        capture_output=True, timeout=50
    )
    require(result.returncode == 0, "LOCAL_REPORT_READY_GITHUB_UPLOAD_FAILED")
    print("PUBLISHED:", result.stdout.decode("utf-8").strip())


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        print("APA_STATUS: BLOCKED_NO_MODEL_CHANGES")
        print("ERROR:", type(error).__name__ + ": " + str(error))
        sys.exit(2)
