"""Orchestrate the existing brief, library pack, spatial checks and BIM compiler."""
from __future__ import annotations

from pathlib import Path

import archicad_authored_native_plan as NATIVE
import archicad_project_accelerator as APA
import archicad_semantic_brief as BRIEF
import archicad_semantic_spatial as SPATIAL


SCHEMA = "apa-project-design/1"


def compile_design(intent):
    fields = {"schemaVersion", "brief", "cseCandidate", "variants"}
    if not isinstance(intent, dict) or set(intent) != fields or intent["schemaVersion"] != SCHEMA:
        raise ValueError("APA_PROJECT_DESIGN_INPUT_FIELDS_REQUIRED")
    brief = intent["brief"]
    normalized = APA.compile_project_brief(brief)
    pack = APA.compile_project_library_pack(brief, intent["cseCandidate"])
    variants = intent["variants"]
    if not isinstance(variants, list) or not 1 <= len(variants) <= 12:
        raise ValueError("APA_DESIGN_REQUIRES_EXPLICIT_VARIANTS")
    output, seen = [], set()
    for row in variants:
        needed = {"id", "layout", "storyHeights"}
        if not isinstance(row, dict) or not needed <= set(row) <= needed | {"floorPlans"}:
            raise ValueError("APA_DESIGN_VARIANT_FIELDS_REQUIRED")
        variant = BRIEF._id(row["id"], "DESIGN_VARIANT_ID")
        if variant in seen:
            raise ValueError("APA_DESIGN_DUPLICATE_VARIANT_ID")
        seen.add(variant)
        result = dict(id=variant, inputHash=APA.RUN.digest(row))
        try:
            candidate = NATIVE.compile_candidate(brief, pack, row["layout"], row["storyHeights"],
                                               None, floor_plans=row.get("floorPlans"), design_only=True)
        except ValueError as exc:
            result.update(status="INVALID_VARIANT", reason=str(exc),
                          requirements=[dict(req, status="NOT_EVALUATED", bimOperationIds=[])
                                        for req in normalized["constraints"]])
        else:
            result.update(status="REQUIREMENTS_OPEN" if candidate["requiredOpenIds"] else "DESIGN_CHECKS_REVIEWABLE",
                          candidate=candidate)
        output.append(result)
    return dict(schemaVersion=SCHEMA, status="DESIGN_VARIANTS_REVIEWED",
                inputHash=APA.RUN.digest(intent), brief=normalized, projectLibraryPack=pack,
                variants=output, nativeWriteCalls=0, executionPermission=False,
                architecturalApproval="PENDING", engineeringApproved=False, normativeApproved=False)


def select_variant(intent, variant_id):
    report = compile_design(intent)
    result = next((row for row in report["variants"] if row["id"] == variant_id), None)
    if result is None or result["status"] != "DESIGN_CHECKS_REVIEWABLE":
        raise ValueError("APA_DESIGN_VARIANT_MISSING_OR_REQUIRED_CHECKS_OPEN")
    if report["brief"]["mode"] != "ADAPT_EXISTING":
        raise ValueError("APA_DESIGN_REQUIRES_EXACT_TEST_PLN_BRIEF_BEFORE_NATIVE_PREFLIGHT")
    row = next(row for row in intent["variants"] if row["id"] == variant_id)
    return dict(schemaVersion="apa-authored-project/1", projectId=report["brief"]["projectId"],
                units="meters", brief=intent["brief"], cseCandidate=intent["cseCandidate"],
                **{key: row[key] for key in row if key != "id"})


def changes_between(previous, current, variant):
    from archicad_local_modules import dependency_impact

    reports = [compile_design(doc) for doc in (previous, current)]
    if reports[0]["brief"]["projectId"] != reports[1]["brief"]["projectId"]:
        raise ValueError("APA_DESIGN_CHANGE_PROJECT_ID_MISMATCH")
    rows = [next((r for r in doc["variants"] if r["id"] == variant and "candidate" in r), None)
            for doc in reports]
    if any(row is None for row in rows):
        raise ValueError("APA_DESIGN_COMPARE_REQUIRES_TWO_VALID_VARIANT_INPUTS")
    before, after = [row["candidate"] for row in rows]
    sources = [next(row for row in doc["variants"] if row["id"] == variant) for doc in (previous, current)]
    space_before, space_after = [
        SPATIAL.compile_spatial(doc["brief"], report["projectLibraryPack"], row["layout"])
        for doc, report, row in zip((previous, current), reports, sources)]
    node_facts = []
    for report, space, candidate, source in zip(reports, (space_before, space_after), (before, after), sources):
        facts = {}
        edges = set()
        for story in report["brief"]["stories"]:
            sid = story["id"]
            key = "story:" + sid
            facts[key] = dict(story, height=source["storyHeights"][sid])
            edges.add((key, "review:documentation"))
        for room in space["rooms"]:
            key = "room:" + room["id"]
            facts[key] = room
            edges.add(("story:" + room["storyId"], key))
            edges.update((key, "review:" + area) for area in ("areas", "facades", "sections", "documentation"))
        for member in space["bearingLines"]:
            key = "bim:native-" + member["id"]
            edges.add(("story:" + member["storyId"], key))
        for path in space["loadPaths"]:
            edges.add(("bim:native-" + path["lowerMemberId"], "bim:native-" + path["upperMemberId"]))
        for operation in candidate["graph"]["operations"]:
            key = "bim:" + operation["id"]
            facts[key] = operation
            if operation["command"] == "CreateSlabs":
                edges.add(("story:" + operation["id"].removeprefix("native-slab-"), key))
            if operation["command"] in ("CreateDoors", "CreateWindows"):
                host = next(iter(operation["params"].values()))[0]["ownerWallId"]["guid"]["$createdGuid"]
                edges.add(("bim:" + host, key))
            edges.update((key, "review:" + check) for check in ("facades", "sections", "documentation"))
        for req in candidate["requirements"]:
            key = "requirement:" + req["id"]
            facts[key] = req
            edges.update(("bim:" + sid, key) for sid in req["bimOperationIds"])
            if req.get("criterion", {}).get("kind") == "AREA_TARGET":
                edges.add(("review:areas", key))
            if req.get("criterion", {}).get("kind") == "STAIR_LINK":
                edges.update(("story:" + req["criterion"][slot], key) for slot in ("lowerStoryId", "upperStoryId"))
            if req.get("criterion", {}).get("kind") in ("ENTRANCE", "ROOM_CONNECTION", "ACCESS_PATH"):
                edges.update(("room:" + req["criterion"][slot], key) for slot in ("from", "to")
                             if req["criterion"][slot] != BRIEF.EXTERIOR)
        for target in ("areas", "facades", "sections", "documentation"):
            facts["review:" + target] = None
        node_facts.append((facts, edges))
    (old, old_edges), (new, new_edges) = node_facts
    nodes = old.keys() | new.keys()
    changed = sorted(key for key in nodes if key not in old or key not in new or old[key] != new[key])
    # Compare each revision's own graph. Combining reversed edges from two
    # individually valid revisions could otherwise manufacture a cycle.
    impacts = [dependency_impact(sorted(facts), sorted(edges), sorted(set(changed) & facts.keys()))
               for facts, edges in node_facts]
    affected = sorted({key for impact in impacts for key in impact["affected"]})
    return dict(status="DESIGN_CHANGE_REVIEW_REQUIRED" if changed else "DESIGN_UNCHANGED",
                previousHash=reports[0]["inputHash"], currentHash=reports[1]["inputHash"],
                changed=changed, affected=affected, executionPermission=False, nativeWriteCalls=0)


def read_request(path, template_path):
    """Keep source bytes and GPT interpretation separate."""
    import hashlib
    import json

    raw = Path(path).read_bytes()
    return dict(status="GPT_INTERPRETATION_REQUIRED", sourceText=raw.decode("utf-8-sig"),
                sourceSha256=hashlib.sha256(raw).hexdigest(),
                exampleInput=json.loads(Path(template_path).read_text(encoding="utf-8")),
                instructions=["Предложите явно заданные варианты. Сохраните исходный текст и идентификаторы требований.",
                              "Если данных для вариантов мало, сначала верните только brief с openQuestions.",
                              "Задавайте тип и допуск площади только при известной методике.",
                              "Для маршрута через несколько помещений задайте ACCESS_PATH. Минимальную ширину проёма укажите только при наличии требования.",
                              "Отдельно зафиксируйте неизвестные площадки, зоны открывания и межэтажные связи."],
                executionPermission=False, nativeWriteCalls=0)
