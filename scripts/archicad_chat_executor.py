"""Translate a small set of plain Russian instructions into executor requests."""
import argparse
import contextlib
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "scripts" / "archicad_executor.py"
DUMP_CLIENT = ROOT / "archicad-addon" / "Examples" / "model_dump_v1.py"
PORT = 19723
TOL = 1e-7
EVIDENCE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence")) / "chat-executor"


def current_dump():
    spec = importlib.util.spec_from_file_location("model_dump_v1", DUMP_CLIENT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with contextlib.redirect_stdout(io.StringIO()):
        data, metrics = module.dump(EVIDENCE / "planner-model-dump.json", PORT)
    return data, metrics


def refline(element):
    ref = element.get("placement", {}).get("referenceGeometry", {})
    if element.get("type") != "Wall" or ref.get("kind") != "WallReferenceLine" or ref.get("arcAngle") != 0:
        return None
    a, b = ref.get("begin"), ref.get("end")
    if not a or not b:
        return None
    length = math.hypot(float(b["x"])-float(a["x"]), float(b["y"])-float(a["y"]))
    if length <= TOL:
        return None
    return ref, a, b, length


def same_wall_level(a, b, stories):
    if a.get("homeStory") != b.get("homeStory"):
        return False
    ar = a["placement"]["referenceGeometry"]
    br = b["placement"]["referenceGeometry"]
    az = stories.get(a.get("homeStory"), 0.0) + float(ar.get("bottomOffsetFromHomeStory", 0.0))
    bz = stories.get(b.get("homeStory"), 0.0) + float(br.get("bottomOffsetFromHomeStory", 0.0))
    return (abs(az-bz) <= TOL and abs(float(ar.get("height", 0))-float(br.get("height", 0))) <= TOL
            and abs(float(ar.get("thickness", 0))-float(br.get("thickness", 0))) <= TOL)


def endpoint_distance(p, q):
    return math.hypot(float(p["x"])-float(q["x"]), float(p["y"])-float(q["y"]))


def direction(ref):
    dx = float(ref["end"]["x"])-float(ref["begin"]["x"])
    dy = float(ref["end"]["y"])-float(ref["begin"]["y"])
    size = math.hypot(dx, dy)
    return dx/size, dy/size


def latest_continuation_candidates(dump):
    stories = {int(s["index"]): float(s["elevation"]) for s in dump.get("stories", [])}
    walls = [e for e in dump.get("elements", []) if refline(e)]
    result = []
    for candidate in walls:
        ref, begin, end, length = refline(candidate)
        # This MVP identifies appended continuation segments by their short,
        # straight reference lines and a single collinear predecessor.
        if length > 2.5 or candidate.get("homeStory") not in stories:
            continue
        ux, uy = direction(ref)
        predecessors = []
        has_successor_or_branch = False
        for other in walls:
            if other is candidate or not same_wall_level(candidate, other, stories):
                continue
            oref, oa, ob, _ = refline(other)
            ox, oy = direction(oref)
            same_axis = ux*ox + uy*oy >= 1.0 - 1e-6
            if endpoint_distance(begin, ob) <= TOL and same_axis:
                predecessors.append(other)
            if endpoint_distance(end, oa) <= TOL or endpoint_distance(end, ob) <= TOL:
                has_successor_or_branch = True
        if len(predecessors) != 1 or has_successor_or_branch:
            continue
        result.append({"guid": candidate["guid"], "homeStory": candidate["homeStory"],
                       "begin": begin, "end": end, "length": length,
                       "predecessorGuid": predecessors[0]["guid"],
                       "selectionRule": "short straight Wall with one collinear Wall joined at begin and an unjoined end"})
    return result


def proposed_wall_colliders(dump, selection, length):
    source = next(e for e in dump["elements"] if e["guid"].lower() == selection["guid"].lower())
    ref = source["placement"]["referenceGeometry"]
    ux, uy = direction(ref)
    start = selection["end"]
    end = {"x": float(start["x"])+ux*length, "y": float(start["y"])+uy*length}
    nx, ny = -uy, ux
    half = float(ref["thickness"])/2
    corners = [(x+nx*side, y+ny*side) for x, y in ((start["x"], start["y"]), (end["x"], end["y"]))
               for side in (-half, half)]
    target = ((min(p[0] for p in corners), max(p[0] for p in corners)),
              (min(p[1] for p in corners), max(p[1] for p in corners)))
    stories = {int(s["index"]): float(s["elevation"]) for s in dump.get("stories", [])}
    z0 = stories[source["homeStory"]] + float(ref.get("bottomOffsetFromHomeStory", 0.0))
    z1 = z0 + float(ref["height"])
    collisions = []
    for element in dump.get("elements", []) + dump.get("unresolvedBodyOwners", []):
        if element["guid"].lower() == source["guid"].lower():
            continue
        for body in element.get("bodies", []):
            pts = body.get("vertices", [])
            if not pts:
                continue
            box = tuple((min(float(p[i]) for p in pts), max(float(p[i]) for p in pts)) for i in range(3))
            overlap = [min(target[i][1], box[i][1])-max(target[i][0], box[i][0]) for i in range(2)]
            overlap.append(min(z1, box[2][1])-max(z0, box[2][0]))
            if all(v > TOL for v in overlap):
                collisions.append(element["guid"])
                break
    return sorted(set(collisions))


def instruction_to_request(instruction, mode, dump):
    text = instruction.strip().lower().replace("ё", "е")
    wall_verb = any(token in text for token in ("продолж", "удлин", "добавь к стен"))
    mentions_wall = any(token in text for token in ("стен", "эту стену"))
    if wall_verb and mentions_wall:
        match = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:м\b|метр(?:а|ов)?\b)", text)
        if not match:
            return {"status": "NEEDS_SELECTION", "reason": "Укажите длину продолжения в метрах.", "instruction": instruction}
        length = float(match.group(1).replace(",", "."))
        if length <= 0 or length > 20:
            return {"status": "NEEDS_SELECTION", "reason": "Длина должна быть больше 0 и не более 20 метров.", "instruction": instruction}
        candidates = latest_continuation_candidates(dump)
        if len(candidates) != 1:
            return {"status": "NEEDS_SELECTION", "instruction": instruction,
                    "reason": "В текущей геометрии не найден единственный конец цепочки стен.",
                    "candidates": candidates[:12]}
        if len(candidates) == 1:
            source_guid = candidates[0]["guid"]
            colliders = proposed_wall_colliders(dump, candidates[0], length)
            if colliders:
                return {"status": "BLOCKED", "instruction": instruction,
                        "reason": "Вычисленный коридор продолжения пересекает геометрию модели.",
                        "selectedGuid": source_guid, "colliderGuids": colliders[:20]}
            return {"status": "PLANNED", "request": {"action": "create_wall", "mode": mode,
                        "sourceGuid": source_guid, "length": length},
                    "selectedGuid": source_guid, "selection": candidates[0]}

    if "окн" in text and any(token in text for token in ("постав", "размест", "установ")):
        hosted = {str(e.get("relationships", {}).get("hostGuid", "")).lower() for e in dump.get("elements", [])}
        candidates = []
        for element in dump.get("elements", []):
            ref = element.get("placement", {}).get("referenceGeometry", {})
            bodies = element.get("bodies", [])
            if (element.get("type") == "Wall" and ref.get("kind") == "WallReferenceLine"
                    and ref.get("arcAngle") == 0 and ref.get("referenceLineLocation") == 1
                    and element.get("guid", "").lower() not in hosted and len(bodies) == 1
                    and bodies[0].get("closed") and len(bodies[0].get("vertices", [])) == 8
                    and len(bodies[0].get("faces", [])) == 6):
                candidates.append({"guid": element["guid"], "homeStory": element.get("homeStory"),
                                   "begin": ref.get("begin"), "end": ref.get("end")})
        return {"status": "NEEDS_SELECTION", "instruction": instruction,
                "reason": "Нужно выбрать конкретную Wall среди кандидатов для Window.",
                "candidates": candidates[:12]}

    if "перекрыт" in text and any(token in text for token in ("сделай", "создай", "построй")):
        return {"status": "PLANNED", "request": {"action": "create_slab", "mode": mode},
                "selection": "Existing simple Slab contour is selected by the proven executor planner."}

    return {"status": "UNSUPPORTED_INSTRUCTION", "instruction": instruction,
            "supportedIntents": ["продолжить стену на N метров", "поставить окно (с выбором стены)",
                                 "создать перекрытие по существующему Slab контуру"]}


def run(instruction, mode="execute"):
    if mode not in ("dry-run", "execute"):
        raise ValueError("mode must be dry-run or execute")
    dump, metrics = current_dump()
    planned = instruction_to_request(instruction, mode, dump)
    if planned["status"] != "PLANNED":
        return planned
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    request_path = EVIDENCE / "executor-request.json"
    request_path.write_text(json.dumps(planned["request"], ensure_ascii=False, indent=2), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(EXECUTOR), str(request_path)], cwd=ROOT,
                          text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=900)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "BLOCKED", "instruction": instruction,
                "reason": "Executor did not return a single JSON response.",
                "returnCode": proc.returncode, "stdoutTail": proc.stdout[-2000:], "stderrTail": proc.stderr[-2000:],
                "executorRequest": planned["request"]}
    status = result.get("status", "BLOCKED")
    return {"status": status if status in ("PASS", "DRY_RUN") else "BLOCKED",
            "instruction": instruction, "selectedGuid": planned.get("selectedGuid"),
            "executorRequest": planned["request"], "executorResult": result,
            "plannerEvidence": {"modelElementCount": len(dump.get("elements", [])),
                               "dumpCounts": dump.get("counts"), "selection": planned.get("selection")},
            "retained": result.get("retained", False), "returnCode": proc.returncode}


def load_input(value):
    if value.lstrip().startswith("{"):
        payload = json.loads(value)
        return payload["instruction"], payload.get("mode", "execute")
    candidate = Path(value)
    if candidate.is_file():
        payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        return payload["instruction"], payload.get("mode", "execute")
    return value, "execute"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instruction", help="Russian instruction text or JSON request file")
    parser.add_argument("--mode", choices=("dry-run", "execute"), default=None)
    args = parser.parse_args()
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        instruction, input_mode = load_input(args.instruction)
        response = run(instruction, args.mode or input_mode)
        print(json.dumps(response, ensure_ascii=False, indent=2))
        if response.get("status") not in ("PASS", "DRY_RUN", "NEEDS_SELECTION", "UNSUPPORTED_INSTRUCTION"):
            raise SystemExit(2)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
