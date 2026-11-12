"""Three opt-in ezdxf 1.4.5 source-geometry reports for the existing APA router."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

import apa_high_density_readonly_v2 as V2

NAMESPACE = "APADXFGeometryC1"
SCHEMA = "APA_DXF_GEOMETRY_C1"
COMMANDS = {"DXFWorldPaths": "paths", "DXFClosedContours": "contours",
            "DXFRepeatedAssemblies": "assemblies"}
MAX_DECOMPOSED = 50000


def path_data(entity, origin=(0, 0, 0)):
    from ezdxf.path import make_path
    path = make_path(entity)
    def point(v):
        return [round(float(v[i]) - origin[i], 9) for i in range(3)]
    commands = [{"command": "MOVE_TO", "pointRoles": ["end"], "points": [point(path.start)]}]
    for command in path:
        commands.append({"command": command.type.name, "pointRoles": list(command._fields),
                         "points": [point(p) for p in command]})
    return {"closed": bool(path.is_closed), "commands": commands,
            "curveRepresentation": "EZDXF_BEZIER_APPROXIMATION" if any(
                x["command"].startswith("CURVE") for x in commands) else "LINEAR"}


def analyze(doc, action):
    from ezdxf.disassemble import recursive_decompose
    from ezdxf.math import Vec3
    rows, unsupported, groups = [], Counter(), defaultdict(list)
    total = visited = 0
    for parent in doc.modelspace():
        if action == "assemblies" and parent.dxftype() != "INSERT":
            continue
        origin = parent.ocs().to_wcs(parent.dxf.insert) if action == "assemblies" else Vec3()
        assembly, complete = [], True
        for entity in recursive_decompose([parent]):
            visited += 1
            V2.require(visited <= MAX_DECOMPOSED, "C1_DECOMPOSITION_LIMIT")
            try:
                data = path_data(entity, origin)
            except TypeError:
                unsupported[entity.dxftype()] += 1
                complete = False
                continue
            provenance = {"parentHandle": parent.dxf.handle, "parentType": parent.dxftype(),
                          "parentLayer": parent.dxf.layer, "entityType": entity.dxftype(),
                          "entityLayer": entity.dxf.layer}
            if action == "assemblies":
                assembly.append(data)
            elif action == "paths" or data["closed"]:
                total += 1
                if len(rows) < V2.SAMPLE_LIMIT:
                    rows.append({**provenance, **data})
        if action == "assemblies" and complete and assembly:
            # Compare transformed geometry after translation only. Rotations and
            # scales remain significant; block names are not geometry evidence.
            signature = sorted(json.dumps(x, sort_keys=True) for x in assembly)
            digest = hashlib.sha256(json.dumps(signature).encode()).hexdigest()
            groups[digest].append({"handle": parent.dxf.handle, "block": parent.dxf.name,
                                   "insertWCS": list(origin), "primitiveCount": len(assembly)})
    if action == "assemblies":
        repeats = [{"geometrySHA256": k, "instances": V2.sample(v)}
                   for k, v in sorted(groups.items()) if len(v) > 1]
        result = {"repeatedAssemblies": V2.sample(repeats), "matching": "TRANSLATION_ONLY",
                  "unsupportedGeneratedEntitiesExcluded": True,
                  "sourceAssemblyCompletenessVerified": False}
    else:
        result = {"paths": V2.sample(rows, total), "closedOnly": action == "contours"}
    result.update(entitiesDecomposed=visited, unsupportedEntityTypes=dict(unsupported),
                  coordinateFrame="DXF_WCS", insunitsCode=doc.header.get("$INSUNITS", 0),
                  unitConversionApplied=False, coordinateRoundingDecimals=9,
                  planarityVerified=False,
                  uncertainties=["Scale and BIM semantics not calibrated", "XCLIP is not applied by upstream decomposition",
                                 "Curves may be represented by approximate Bezier paths",
                                 "Closed paths are contour candidates; holes, intersections and constructibility unverified"],
                  bimElementsInferred=False, plannerWrites=0)
    return result


def inputs(action, params):
    V2.require(action in COMMANDS.values() and set(params) == {"a", "output"}
               and all(isinstance(x, str) and x for x in params.values()), "C1_INVALID_PARAMETERS")
    source = V2.input_file(params["a"], ".dxf")
    return source, V2.output_file(params["output"], source)


def execute(action, params):
    source, output = inputs(action, params)
    V2.require(importlib.metadata.version("ezdxf") == "1.4.5", "C1_EZDXF_VERSION_DRIFT")
    before = V2.digest(source)
    import ezdxf
    result = analyze(ezdxf.readfile(str(source)), action)
    V2.require(V2.digest(source) == before, "C1_SOURCE_CHANGED")
    evidence = {"schema": SCHEMA, "action": action, "source": {"name": source.name, "sha256": before},
                "adapterSha256": V2.digest(__file__), "sourceUnchanged": True,
                "result": result, "nativeCalls": 0, "modelWrites": 0}
    with output.open("x", encoding="utf8") as stream:
        json.dump(evidence, stream, indent=2, ensure_ascii=False, allow_nan=False)
    return evidence


def call(action, params):
    source, output = inputs(action, params)
    before, adapter = V2.digest(source), V2.digest(__file__)
    process = subprocess.run([str(V2.verified_python()), "-B", str(Path(__file__).resolve()), action,
                              "--a", str(source), "--output", str(output)], capture_output=True,
                             text=True, timeout=1200)
    V2.require(process.returncode == 0, "C1_VENDOR_FAILED:" + process.stderr[-1200:])
    V2.require(output.is_file() and output.stat().st_size < 200 * 1024**2, "C1_REPORT_INVALID")
    data = json.loads(output.read_text(encoding="utf8"))
    V2.require(data.get("schema") == SCHEMA and data.get("action") == action
               and before == V2.digest(source) and adapter == V2.digest(__file__)
               and data.get("adapterSha256") == adapter and data.get("sourceUnchanged") is True
               and data.get("source") == {"name": source.name, "sha256": before}
               and data.get("modelWrites") == data.get("nativeCalls") == 0, "C1_EVIDENCE_MISMATCH")
    return data


def register(router):
    V2.verified_python()
    contracts, handlers = {}, {}
    for name, action in COMMANDS.items():
        contracts[name] = {"name": name, "version": "1", "category": "APA_DXF_SOURCE_GEOMETRY",
            "parameters": {"type": "object", "properties": {k: {"type": "string", "minLength": 1} for k in ("a", "output")},
                           "required": ["a", "output"], "additionalProperties": False},
            "returns": {"type": "object", "required": ["schema", "source", "result", "sourceUnchanged", "nativeCalls", "modelWrites"]}}
        handlers[name] = (lambda act: lambda **kw: call(act, kw))(action)
    router.add_local_provider(NAMESPACE, contracts, handlers, SCHEMA, {name: [] for name in COMMANDS})
    for name in COMMANDS:
        key = "AddOn." + NAMESPACE + "." + name
        router.review_policy(key, "READ_ONLY", "READ_ONLY", {"source": SCHEMA, "sha256": router.contract_hash(key)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=COMMANDS.values())
    parser.add_argument("--a", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    execute(args.action, {"a": args.a, "output": args.output})
