"""Existing IfcOpenShell serializers/geometry utilities, no new geometry engine."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

import apa_ifc_artifacts_b2 as B2
V2 = B2.V2
NAMESPACE = "APAIFCGeometryB3"
SCHEMA = "APA_IFC_GEOMETRY_B3"
COMMANDS = {"IFCGeometryOBJ": "obj", "IFCGeometryGLB": "glb", "IFCGeometryBounds": "bounds"}
FILES = {"obj": "model.obj", "glb": "model.glb", "bounds": "geometry-bounds.json"}


def readback(path, action):
    V2.require(path.is_file() and path.stat().st_size < 200 * 1024**2, "B3_ARTIFACT_INVALID")
    if action == "obj":
        vertices = faces = 0
        with path.open(encoding="utf8") as stream:
            for line in stream:
                vertices += line.startswith("v ")
                faces += line.startswith("f ")
        V2.require(vertices > 0 and faces > 0, "B3_OBJ_EMPTY")
        mtl = path.with_suffix(".mtl")
        V2.require(mtl.is_file(), "B3_MTL_MISSING")
        details = {"vertices": vertices, "faces": faces, "mtlSHA256": V2.digest(mtl)}
    elif action == "glb":
        with path.open("rb") as stream:
            magic, version, length = struct.unpack("<4sII", stream.read(12))
            V2.require(magic == b"glTF" and version == 2 and length == path.stat().st_size, "B3_GLB_HEADER_INVALID")
            chunk_length, kind = struct.unpack("<II", stream.read(8))
            V2.require(kind == 0x4e4f534a and chunk_length <= length - 20, "B3_GLB_JSON_CHUNK_INVALID")
            # Only the explicitly typed JSON chunk enters a JSON parser.
            document = json.loads(stream.read(chunk_length).decode("utf8"))
            V2.require(document.get("asset", {}).get("version") == "2.0" and document.get("meshes"), "B3_GLB_EMPTY")
            details = {"meshes": len(document["meshes"]), "nodes": len(document.get("nodes", []))}
    else:
        document = json.loads(path.read_text(encoding="utf8"))
        details = {"elements": document["elements"]["total"], "coordinateFrame": document["coordinateFrame"]}
    return {"name": path.name, "format": action, "bytes": path.stat().st_size,
            "sha256": V2.digest(path), **details}


def execute(action, params):
    V2.require(action in FILES, "B3_UNKNOWN_ACTION")
    source, out = B2.inputs("extract", params)
    V2.require(importlib.metadata.version("ifcopenshell") == "0.8.5", "B3_VENDOR_VERSION_DRIFT")
    before = V2.digest(source)
    import ifcopenshell
    import ifcopenshell.geom as geom
    import ifcopenshell.util.shape as shape_util
    from ifcopenshell.util.selector import filter_elements
    out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="private-ifc-", dir=out) as temporary:
        copy = Path(temporary) / "model.ifc"
        shutil.copyfile(source, copy)
        V2.require(V2.digest(copy) == before, "B3_COPY_HASH_MISMATCH")
        model = ifcopenshell.open(str(copy))
        selected = sorted(filter_elements(model, params["query"]), key=lambda x: x.id())
        V2.require(selected and all(x.is_a("IfcProduct") and getattr(x, "Representation", None) for x in selected),
                   "B3_REPRESENTED_PRODUCTS_REQUIRED")
        settings = geom.settings()
        settings.set("apply-default-materials", True)
        settings.set("use-world-coords", action != "glb")
        settings.set("convert-back-units", False)
        iterator = geom.iterator(settings, model, 1, include=selected)
        artifact = out / FILES[action]
        serializer = None
        if action in {"obj", "glb"}:
            ss = geom.serializer_settings()
            ss.set("use-element-guids", True)
            serializer = geom.serializers.obj(str(artifact), str(artifact.with_suffix(".mtl")), settings, ss) if action == "obj" else geom.serializers.gltf(str(artifact), settings, ss)
            serializer.setFile(model)
            serializer.setUnitNameAndMagnitude("METER", 1.0)
            serializer.writeHeader()
        processed, rows = set(), []
        V2.require(iterator.initialize(), "B3_GEOMETRY_ITERATOR_EMPTY")
        while True:
            shape = iterator.get()
            processed.add(shape.id)
            if serializer:
                serializer.write(shape)
            else:
                vertices = shape_util.get_vertices(shape.geometry)
                low, high = shape_util.get_bbox(vertices)
                if len(rows) < V2.SAMPLE_LIMIT:
                    rows.append({"stepId": shape.id, "globalId": shape.guid,
                                 "min": low.tolist(), "max": high.tolist()})
            if not iterator.next():
                break
        if serializer:
            serializer.finalize()
            del serializer
        V2.require(processed == {x.id() for x in selected}, "B3_PARTIAL_GEOMETRY_CONVERSION")
        if action == "bounds":
            artifact.write_text(json.dumps({"coordinateFrame": "IFC_WORLD_SI_METRES",
                                           "elements": V2.sample(rows, len(processed))}, indent=2), encoding="utf8")
        metadata = readback(artifact, action)
    V2.require(before == V2.digest(source), "B3_SOURCE_CHANGED")
    evidence = {"schema": SCHEMA, "action": action, "source": {"name": source.name, "sha256": before},
                "adapterSha256": V2.digest(__file__), "artifact": metadata,
                "processedElements": len(processed), "sourceUnchanged": True,
                "backend": "ifcopenshell.geom 0.8.5 Python API", "nativeCalls": 0, "modelWrites": 0,
                "limitations": ["Triangulated geometry; no native BIM acceptance", "Georeferencing calibration unverified"]}
    with (out / "report.json").open("x", encoding="utf8") as stream:
        json.dump(evidence, stream, indent=2, ensure_ascii=False, allow_nan=False)
    return evidence


def call(action, params, python):
    V2.require(action in FILES, "B3_UNKNOWN_ACTION")
    source, out = B2.inputs("extract", params)
    before, adapter = V2.digest(source), V2.digest(__file__)
    process = subprocess.run([str(python), "-B", str(Path(__file__).resolve()), action,
                              "--parameters", json.dumps(params)], capture_output=True, text=True, timeout=1200)
    V2.require(process.returncode == 0, "B3_VENDOR_FAILED:" + process.stderr[-1200:])
    report = out / "report.json"
    V2.require(report.is_file() and report.stat().st_size < 200 * 1024**2, "B3_REPORT_INVALID")
    data = json.loads(report.read_text(encoding="utf8"))
    V2.require(data.get("schema") == SCHEMA and data.get("action") == action
               and data.get("source") == {"name": source.name, "sha256": before}
               and V2.digest(source) == before and V2.digest(__file__) == adapter
               and data.get("adapterSha256") == adapter and data.get("sourceUnchanged") is True
               and data.get("artifact") == readback(out / FILES[action], action)
               and data.get("modelWrites") == data.get("nativeCalls") == 0, "B3_EVIDENCE_MISMATCH")
    return data


def register(router, python):
    python = Path(python).resolve(strict=True)
    contracts, handlers = {}, {}
    for name, action in COMMANDS.items():
        props = B2.fields("extract")
        contracts[name] = {"name": name, "version": "1", "category": "APA_IFC_GEOMETRY",
            "parameters": {"type": "object", "properties": props, "required": list(props), "additionalProperties": False},
            "returns": {"type": "object", "required": ["schema", "source", "artifact", "processedElements", "nativeCalls", "modelWrites"]}}
        handlers[name] = (lambda act: lambda **kw: call(act, kw, python))(action)
    router.add_local_provider(NAMESPACE, contracts, handlers, SCHEMA, {name: [] for name in COMMANDS})
    for name in COMMANDS:
        key = "AddOn." + NAMESPACE + "." + name
        router.review_policy(key, "READ_ONLY", "READ_ONLY", {"source": SCHEMA, "sha256": router.contract_hash(key)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=FILES)
    parser.add_argument("--parameters", required=True)
    args = parser.parse_args()
    execute(args.action, json.loads(args.parameters))
