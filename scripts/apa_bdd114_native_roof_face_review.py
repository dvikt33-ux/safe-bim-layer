"""BDD block 1.14: exact native ROOF-face clearance and accepted Wall joint.

Only source-qualified read-only native BREP; reuses existing APA authored-geometry
planar face extraction. No custom BIM engine, no native mutation or PLN save.
"""
from __future__ import annotations
import base64
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable\scripts")
WORKING = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
ORIGINAL = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
WORKING_SHA = "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
ORIGINAL_SHA = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
CORE_SHA = "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b"
DYNAMIC_SHA = "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8"
SELECTOR_SHA = "32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce"
ROOF_GUID = "f0d643a1-b236-4dfc-844a-98424a12b9b7"
NORTH_GUID = "7b332594-ab82-43b4-bfc2-ab5ad549c2c9"
PROTOTYPE_GUID = "b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
SOURCE_POSITIONS = [9.255, 8.838, 8.420, 8.008, 7.595, 6.995, 6.395]
BRIDGE = "dvikt33-ux/safe-bim-bridge"
SOURCE_REPORT_PATH = "safe-bim-mailbox/gpt-live/results/apa-bdd-114-spatial-20261017T135836Z-ef6f985e.json"
SOURCE_REPORT_SHA1 = "90045930ec747d648eda8422a6537ee0b09a0f7d"


def require(condition, error):
    if not condition:
        raise ValueError(error)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_report():
    endpoint = f"repos/{BRIDGE}/contents/{SOURCE_REPORT_PATH}?ref=main"
    result = subprocess.run(["gh", "api", endpoint],
                            capture_output=True, timeout=45)
    require(result.returncode == 0, "SOURCE_SPATIAL_REPORT_ACCESS_FAILED")
    obj = json.loads(result.stdout.decode("utf8"))
    data = base64.b64decode(obj["content"])
    git_sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    require(git_sha == obj["sha"] == SOURCE_REPORT_SHA1,
            "SOURCE_SPATIAL_REPORT_CHANGED")
    return json.loads(data.decode("utf-8"))


def aabb(verts):
    return [(min(p[i] for p in verts), max(p[i] for p in verts)) for i in range(3)]


def volumetric_aabb_overlaps(left, right, tol=1e-8):
    return all(left[i][0] < right[i][1]-tol and right[i][0] < left[i][1]-tol for i in range(3))


def body_boxes(row):
    return [aabb(body["vertices"]) for body in row["bodies"] if body.get("vertices")]


def projected_face_polygon(roof, face):
    from shapely.geometry import Polygon
    body = roof["bodies"][face["bodyIndex"]]
    outlines = body["faces"][face["faceIndex"]]["contours"]
    vertices = body["vertices"]
    rings = [[(vertices[i][0], vertices[i][1]) for i in contour] for contour in outlines]
    p = Polygon(rings[0], rings[1:])
    require(p.is_valid, "NATIVE_ROOF_FACE_INVALID_XY_POLYGON")
    return p


def polygon_vertex_xy(poly):
    # Plane elevation is linear, so its min/max over a polygon are attained at
    # boundary vertices. Preserve disjoint pieces and projected contour holes.
    if poly.is_empty:
        return []
    if poly.geom_type == "Polygon":
        coords = list(poly.exterior.coords)
        for ring in poly.interiors:
            coords.extend(ring.coords)
        return coords
    if hasattr(poly, "geoms"):
        return [pt for part in poly.geoms for pt in polygon_vertex_xy(part)]
    return []


def minimum_native_roof_height_over_footprint(roof, source_geometry, footprint):
    elevations = []
    checked_faces = 0
    for face in source_geometry.planar_faces(roof):
        n, d = face["normal"], face["distance"]
        if abs(n[2]) <= 0.25:
            continue
        actual_face = projected_face_polygon(roof, face)
        overlap = footprint.intersection(actual_face)
        if overlap.is_empty or overlap.area < 1e-12:
            continue
        checked_faces += 1
        for x, y in polygon_vertex_xy(overlap):
            z = (d - n[0]*x - n[1]*y) / n[2]
            if math.isfinite(z):
                elevations.append(z)
    require(elevations, "ROOF_SLOPED_FACE_PROJECTION_MISSING_NEAR_STUD")
    return min(elevations), checked_faces


def run():
    for name, sha in (
        ("archicad_project_accelerator.py", CORE_SHA),
        ("archicad_dynamic_commands.py", DYNAMIC_SHA),
        ("archicad_strategy_discovery.py", SELECTOR_SHA),
    ):
        require(digest(STABLE / name) == sha, "STABLE_APA_MODULE_DRIFT:" + name)
    require(digest(WORKING) == WORKING_SHA and digest(ORIGINAL) == ORIGINAL_SHA,
            "BDD_PLN_SOURCE_OR_SAVED_BASELINE_DRIFT")
    source = pinned_report()
    require(source["status"] == "NATIVE_SPATIAL_CANDIDATES_REQUIRE_JUNCTION_REVIEW"
            and len(source["members"]) == 7
            and source["contactCount"] == 8 and source["modelWrites"] == 0,
            "PRIOR_SPATIAL_PRECHECK_INCONSISTENT")
    require(all(abs(member["x"] - 9.37) < 1e-8
                and abs(member["y"] - expected) < 1e-8
                for member, expected in zip(source["members"], SOURCE_POSITIONS)),
            "EXPECTED_SEVEN_STUD_COORDINATES_CHANGED")

    sys.path.insert(0, str(STABLE))
    from shapely.geometry import box
    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_connected_components as C

    RUN.bind_authorized_saved_copy(
        19727, str(WORKING), WORKING.stem, WORKING_SHA,
        "BDD_BLOCK_114_BREP_ROOF_JUNCTION_READ_ONLY_NOT_WRITE_AUTHORIZATION"
    )
    folder = Path(tempfile.mkdtemp(prefix="apa-bdd114-native-roof-"))
    (folder / "raw").mkdir()
    api = APA.EvidenceAPI(APA.native_transport, folder / "raw", execute=False)
    RUN.guarded_project_for_read(api)
    require(APA.archicad29(api).get("buildNumber") == 5101, "WRONG_ARCHICAD_BUILD")
    guids = set(APA.inventory_guids(api))
    require(len(guids) == 290 and {ROOF_GUID, NORTH_GUID, PROTOTYPE_GUID} <= guids,
            "BDD_ACCEPTED_MODEL_INVENTORY_DRIFT")
    dump = C.G.normalize_dump(api("GetModelDumpV1", {}))
    native = {r["guid"].lower(): r for r in dump["elements"]}
    require(set(native) == guids, "BDD_NATIVE_DUMP_AND_CURRENT_INVENTORY_DIFFER")
    roof = native[ROOF_GUID]
    north = native[NORTH_GUID]
    require(roof["type"] == "Roof" and north["type"] == "Wall",
            "BDD_EXPECTED_ROOF_NORTH_WALL_CHANGED")
    other_roofs = [g for g,v in native.items() if v["type"] == "Roof" and g != ROOF_GUID]
    require(not other_roofs, "ADDITIONAL_ROOFS_REQUIRE_WHOLE_MODEL_ASSESSMENT")

    roof_results = []
    roof_flags = []
    for member in source["members"]:
        x, y = member["x"], member["y"]
        # Section is the VERIFIED native width (x) 0.1 and depth (y) 0.05.
        area = box(x-.05, y-.025, x+.05, y+.025)
        lower, faces = minimum_native_roof_height_over_footprint(roof, C.G, area)
        clearance = lower-2.9
        result = {
            "index": member["index"],
            "studCenter": [x, y],
            "roofLowestPlanarBREPFaceZOverFootprintM": lower,
            "studTopZ": 2.9,
            "minimumRoofFaceHeightMinusStudTopM": clearance,
            "nativeSlopedFacesSampled": faces,
            "roofAssessment": (
                "PROVEN_SEPARATE_BY_NATIVE_ROOF_FACE_HEIGHT"
                if clearance > .002
                else "ROOF_PHYSICAL_CONTACT_POSSIBLE_REQUIRE_DETAIL"
            ),
        }
        roof_flags.append(result["roofAssessment"])
        roof_results.append(result)

    # Match the top-end joint against both already ACCEPTED source studs in
    # the same wall. No wall geometry is changed or newly constructed here.
    stored_top_studs = []
    for x in (3.53, 7.15):
        parents = [guid for guid, row in native.items()
                   if row.get("type") == "Column"
                   and any(abs(b[0][0]+.05-x) < 1e-4 and
                           abs(b[1][0]+.025-9.255) < 1e-4
                           for b in body_boxes(row) if b)]
        # Column physical bodies may be owned only by ColumnSegment; use
        # actual ColumnSegment relationship rather than root BREP.
        if not parents:
            children = []
            for guid, row in native.items():
                if row.get("type") != "ColumnSegment":
                    continue
                bb = body_boxes(row)
                if (bb and abs((bb[0][0][0]+bb[0][0][1])/2-x) < 1e-4
                        and abs((bb[0][1][0]+bb[0][1][1])/2-9.255) < 1e-4):
                    children.append((guid, row))
        else:
            children = [(guid,row) for guid,row in native.items()
                        if row.get("type") == "ColumnSegment"
                        and row.get("relationships",{}).get("hostGuid","").lower() in parents]
        require(len(children) == 1, "EXISTING_NORTH_STUD_PHYSICAL_PROTOTYPE_AMBIGUOUS")
        child_guid, child = children[0]
        joined = any(volumetric_aabb_overlaps(a,b) for a in body_boxes(child)
                     for b in body_boxes(north))
        stored_top_studs.append({
            "columnSegmentGuid": child_guid,
            "columnCenterX": x,
            "columnCenterY": 9.255,
            "nativeAABBNorthWallOverlap": joined,
        })
    require(all(row["nativeAABBNorthWallOverlap"] for row in stored_top_studs),
            "NORTH_WALL_JUNCTION_NOT_SAME_AS_PREVIOUS_ACCEPTED_STUDS")

    after = set(APA.inventory_guids(api))
    require(after == guids and api.write_attempts == 0,
            "LIVE_BREP_CHECK_MODIFIED_MODEL_OR_INVENTORY")
    require(digest(WORKING) == WORKING_SHA and digest(ORIGINAL) == ORIGINAL_SHA,
            "SAVED_PROJECT_CHANGED_ON_READ")
    roof_clear = all(flag == "PROVEN_SEPARATE_BY_NATIVE_ROOF_FACE_HEIGHT"
                     for flag in roof_flags)
    status = (
        "ROOF_NATIVE_FACE_CLEAR_NORTH_JUNCTION_MATCHES_EXISTING"
        if roof_clear else "ROOF_NATIVE_FACE_CONTACT_REQUIRES_DETAIL"
    )
    report = {
        "schema": "APA_BDD_BLOCK114_NATIVE_ROOF_FACE_REVIEW_V1",
        "status": status,
        "workingPlnGuidCount": 290,
        "candidatePositionsFromSourceReport": SOURCE_REPORT_PATH,
        "roofGuid": ROOF_GUID,
        "nativeRoofFaceAssessments": roof_results,
        "existingNorthJunctionPrecedent": stored_top_studs,
        "northJunctionStatus": "SAME_AABB_JUNCTION_AS_ACCEPTED_1_12_AND_1_13",
        "roofClearAtAllSevenMembers": roof_clear,
        "xCoordinateSource": "GRAPHICALLY_CALIBRATED_NOT_DIMENSION_PRINTED",
        "nextAuthorizationNeeded": (
            "User-approved vector-calibrated X=9.370 before source-qualified "
            "one-shot guarded seven-stud copy; no automatic write permission"
        ),
        "nativeModelWrites": api.write_attempts,
        "automaticWriteAuthorization": False,
        "engineeringLoadOrCodeAcceptance": "NOT_ASSESSED",
    }
    destination = folder / "roof-face-clearance.json"
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf8")
    print("APA_STATUS:", status)
    print("ROOF_CLEAR:", roof_clear, "| GUIDS:", len(after))
    for row in roof_results:
        print("STUD", row["index"], "ROOF_MIN_Z:",
              round(row["roofLowestPlanarBREPFaceZOverFootprintM"],4),
              "CLEARANCE_M:",round(row["minimumRoofFaceHeightMinusStudTopM"],4))
    print("NORTH_JUNCTION:",report["northJunctionStatus"])
    print("MODEL_WRITES: 0")
    print("REPORT:", destination)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remote = "safe-bim-mailbox/gpt-live/results/apa-bdd114-native-roof-" + stamp + "-" + uuid4().hex[:8] + ".json"
    request = folder / "upload.json"
    request.write_text(json.dumps({
        "branch": "main",
        "message": "BDD block114 native roof-face clearance and existing north-junction comparison",
        "content": base64.b64encode(destination.read_bytes()).decode("ascii"),
    }), encoding="utf8")
    response = subprocess.run([
        "gh", "api", "--method", "PUT",
        f"repos/{BRIDGE}/contents/{remote}",
        "--input", str(request), "--jq", ".content.html_url",
    ], capture_output=True, timeout=50)
    require(response.returncode == 0, "ROOF_REPORT_WRITTEN_LOCAL_GITHUB_UPLOAD_FAILED")
    print("PUBLISHED:", response.stdout.decode("utf8").strip())


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print("APA_STATUS: BLOCKED_NO_MODEL_CHANGES")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
