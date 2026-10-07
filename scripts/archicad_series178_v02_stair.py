"""Create one provisional Series 178 central stair in the proven direct skeleton.

Guards: exact Tapir port, project-path substring, active story, skeleton manifest
and all 29 skeleton GUIDs. Creates exactly one Stair, reads it back, records its
GUID immediately, and never saves the PLN.

This is a visual reconstruction pass. Stair dimensions are provisional until
checked against a construction sheet; the verified passport controls only the
central 3.6 m bay and the 3.0 m storey height used here.
"""
from __future__ import annotations
import argparse, json, os, tempfile, urllib.request
from pathlib import Path

SKELETON = Path(tempfile.gettempdir()) / "series178-direct-19725-created.json"
OUT = Path(os.environ.get(
    "SAFE_BIM_MVP_EVIDENCE",
    Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence"
)) / "series178-v02" / "stair.json"


def api(port, command, params=None):
    body = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": params or {},
        },
    }
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}",
        json.dumps(body, ensure_ascii=False).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        env = json.loads(r.read())
    if not env.get("succeeded"):
        raise RuntimeError(f"{command} transport failed")
    result = env.get("result", {}).get("addOnCommandResponse", {})
    if isinstance(result, dict) and result.get("error") is not None:
        raise RuntimeError(f"{command}: {result['error']}")
    return result


def write(value):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def elem(guid):
    return {"elementId": {"guid": guid}}


def live_guids(port):
    return {
        x["elementId"]["guid"].lower()
        for x in api(port, "GetAllElements").get("elements", [])
        if x.get("elementId", {}).get("guid")
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=19725)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument(
        "--expect-project-substring",
        default="SafeBIM_Global_Library_Test_Projects",
    )
    args = ap.parse_args()

    if not SKELETON.is_file():
        raise RuntimeError(f"missing skeleton manifest: {SKELETON}")
    sk = json.loads(SKELETON.read_text(encoding="utf-8-sig"))
    if len(sk.get("wallGuids", [])) != 28 or not sk.get("slabGuid"):
        raise RuntimeError("skeleton manifest must contain 28 walls + 1 slab")

    project = api(args.port, "GetProjectInfo")
    path = project.get("projectPath") or ""
    if args.expect_project_substring.lower() not in path.lower():
        raise RuntimeError(f"wrong project on port {args.port}: {path}")

    stories = api(args.port, "GetStories")
    story_index = int(sk.get("storyIndex", 0))
    if int(stories.get("actStory", -999)) != story_index:
        raise RuntimeError(
            f"active story {stories.get('actStory')} != target {story_index}"
        )
    story = next(
        (s for s in stories.get("stories", []) if int(s["index"]) == story_index),
        None,
    )
    if story is None:
        raise RuntimeError(f"story {story_index} not found")

    live = live_guids(args.port)
    required = {sk["slabGuid"].lower(), *[g.lower() for g in sk["wallGuids"]]}
    missing = sorted(required - live)
    if missing:
        raise RuntimeError(f"skeleton changed; missing GUIDs: {missing[:6]}")

    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8-sig"))
        old_guid = old.get("guid")
        if old_guid and old_guid.lower() in live:
            raise RuntimeError(
                f"v0.2 stair already exists: {old_guid}; refusing duplicate"
            )

    ox = float(sk["originX"])
    oy = float(sk["originY"])
    z0 = float(story.get("level", 0.0))

    # Verified bay: x 9.6..13.2, y 7.8..13.2 relative to skeleton origin.
    # Provisional U-shaped baseline inset from panel centerlines.
    baseline = [
        {"x": ox + 10.20, "y": oy + 8.35},
        {"x": ox + 10.20, "y": oy + 12.20},
        {"x": ox + 12.60, "y": oy + 12.20},
        {"x": ox + 12.60, "y": oy + 8.35},
    ]
    plan = {
        "status": "DRY_RUN" if not args.execute else "PLANNED",
        "port": args.port,
        "projectPath": path,
        "storyIndex": story_index,
        "origin": {"x": ox, "y": oy},
        "bay": {
            "x": [ox + 9.6, ox + 13.2],
            "y": [oy + 7.8, oy + 13.2],
        },
        "baseline": baseline,
        "totalHeight": 3.0,
        "flightWidth": 1.05,
        "stepNum": 18,
        "riserHeight": 3.0 / 18.0,
        "treadDepth": 0.28,
        "dimensionStatus": "PROVISIONAL_VISUAL_RECONSTRUCTION",
        "savedProject": False,
    }
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    result = api(args.port, "CreateStairs", {
        "stairsData": [{
            "baseLinePoints": baseline,
            "zCoordinate": z0,
            "floorIndex": story_index,
            "totalHeight": 3.0,
            "flightWidth": 1.05,
            "stepNum": 18,
            "riserHeight": 3.0 / 18.0,
            "treadDepth": 0.28,
        }]
    })
    rows = result.get("elements", [])
    guids = [x.get("elementId", {}).get("guid") for x in rows]
    guids = [g for g in guids if g]
    if len(guids) != 1:
        raise RuntimeError(f"CreateStairs returned: {rows}")
    guid = guids[0]

    # Persist GUID before any non-essential checks so a partial failure cannot
    # cause an unsafe blind retry.
    evidence = {**plan, "status": "CREATED_NEEDS_READBACK", "guid": guid}
    write(evidence)

    details = api(args.port, "GetDetailsOfElements", {
        "elements": [elem(guid)]
    }).get("detailsOfElements", [])
    boxes = api(args.port, "Get3DBoundingBoxes", {
        "elements": [elem(guid)]
    }).get("boundingBoxes3D", [])

    if len(details) != 1 or details[0].get("type") != "Stair":
        raise RuntimeError(f"stair read-back mismatch: {details}")

    box = boxes[0].get("boundingBox3D") if boxes else None
    evidence.update({
        "status": "PASS",
        "readBack": details[0],
        "boundingBox": box,
        "elementCountAfter": len(live_guids(args.port)),
        "nextPhase": "visual compare stair; then slab opening and corridor access",
    })
    write(evidence)

    try:
        api(args.port, "ChangeSelectionOfElements", {
            "addElementsToSelection": [elem(guid)]
        })
        api(args.port, "FitInWindow", {"elements": [elem(guid)]})
    except Exception:
        pass

    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "error": str(exc),
            "evidence": str(OUT),
            "note": "Do not retry blindly; inspect watcher/evidence first.",
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
