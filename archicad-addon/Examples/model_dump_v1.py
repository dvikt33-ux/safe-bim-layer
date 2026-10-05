"""One command: read the current Archicad model through Tapir GetModelDumpV1.

No PLN identity/path lookup, no model writes. The native command refreshes the
current 3D view. Existing visibility filters remain in force and are declared.
"""
import argparse
import json
import time
import urllib.request
from collections import Counter
from pathlib import Path


def call(command, parameters=None, port=19723, timeout=600):
    request = {"command": "API.ExecuteAddOnCommand", "parameters": {
        "addOnCommandId": {"commandNamespace": "TapirCommand", "commandName": command},
        "addOnCommandParameters": parameters or {}}}
    payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
    started = time.perf_counter()
    with urllib.request.urlopen(urllib.request.Request(
            f"http://127.0.0.1:{port}", payload, {"Content-Type": "application/json"}), timeout=timeout) as response:
        raw = response.read()
    elapsed = time.perf_counter() - started
    envelope = json.loads(raw)
    if not envelope.get("succeeded"):
        raise RuntimeError(envelope)
    result = envelope["result"]["addOnCommandResponse"]
    if "error" in result or "schemaVersion" not in result and command == "GetModelDumpV1":
        raise RuntimeError(result)
    return result, elapsed, raw, payload


def normalize(native):
    if native["nativeBodySlots"] == 0:
        raise ValueError("Native 3D model has zero bodies; full geometry dump is unavailable")
    elements = {e["guid"].lower(): e for e in native["elements"]}
    materials = {m["id"]: m for m in native["materials"]}
    for material in materials.values():
        if material.get("attribute", {}).get("guid"):
            material["guid"] = material["attribute"]["guid"]
    if len(elements) != len(native["elements"]) or len(materials) != len(native["materials"]):
        raise ValueError("Duplicate element or material identity")
    for e in elements.values():
        e["bodies"] = []
        # Object.owner is a native external-object owner, not a proved host.
        # Keep that distinction even when the referenced owner is outside the dump.
        relations = e.get("relationships", {})
        if e["type"] in ("Object", "Lamp") and "hostGuid" in relations:
            owner_guid = relations.pop("hostGuid")
            relations["ownerGuid"] = owner_guid
            relations["nativeField"] = "object.owner"
            relations["ownerResolution"] = "IN_DUMP" if owner_guid.lower() in elements else "OUTSIDE_DUMP_OR_UNRESOLVED"
    # ModelAccess can return a model-only owner for which no BIM header exists.
    # Retain its geometry without inventing a native type or floor assignment.
    unresolved = []
    for e in elements.values():
        if e.get("nativeElementReadError") and e.get("nativeTypeId") == 0:
            e["type"] = None
            e["homeStory"] = None
            e["identityStatus"] = "NATIVE_BODY_OWNER_WITHOUT_READABLE_BIM_HEADER"
            unresolved.append(e)
    holes = 0
    for body in native.pop("bodies"):
        owner = elements[body["parentGuid"].lower()]
        body["vertices"] = [[p["x"], p["y"], p["z"]] for p in body["vertices"]]
        body["vertexCoordinates"] = "ABSOLUTE_PROJECT_XYZ_METERS"
        for face in body["faces"]:
            if face["materialId"] not in materials:
                raise ValueError(f"Missing material {face['materialId']}")
            contours = face["contours"]
            for contour in contours:
                if any(v < 0 or v >= len(body["vertices"]) for v in contour):
                    raise ValueError("Face vertex outside body")
            face["vertices"] = contours[0] if contours else []
            face["holes"] = contours[1:]
            holes += len(face["holes"])
        owner["bodies"].append(body)
    unresolved_guids = {e["guid"].lower() for e in unresolved}
    known = [e for guid, e in elements.items() if guid not in unresolved_guids]
    native["elements"] = known
    native["unresolvedBodyOwners"] = unresolved
    native["counts"] = {
        "elements": len(known), "elementsWithBodies": sum(bool(e["bodies"]) for e in known),
        "unresolvedBodyOwners": len(unresolved),
        "bodies": sum(len(e["bodies"]) for e in elements.values()),
        "vertices": sum(len(b["vertices"]) for e in elements.values() for b in e["bodies"]),
        "faces": sum(len(b["faces"]) for e in elements.values() for b in e["bodies"]),
        "materials": len(materials), "holeContours": holes,
        "elementTypes": dict(Counter(e["type"] for e in known)),
        "bodyTypes": dict(Counter(e["type"] or "UNRESOLVED_MODEL_OWNER" for e in elements.values() for b in e["bodies"]))}
    return native


def dump(output, port=19723):
    started = time.perf_counter()
    native, http_seconds, raw, request = call("GetModelDumpV1", port=port)
    result = normalize(native)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".request.json").write_bytes(request)
    # Retain the actual native response, including native topology and status.
    output.with_suffix(".native-response.json").write_bytes(raw)
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    metrics = {"counts": result["counts"], "nativeSeconds": result["nativeSeconds"],
        "httpSeconds": http_seconds, "totalSeconds": time.perf_counter() - started,
        "nativePayloadBytes": len(raw), "dumpBytes": output.stat().st_size,
        "output": str(output.resolve()), "geometryScope": result["geometryScope"]}
    output.with_suffix(".metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return result, metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=19723)
    parser.add_argument("--out", default="model-dump-v1.json")
    args = parser.parse_args()
    dump(args.out, args.port)
