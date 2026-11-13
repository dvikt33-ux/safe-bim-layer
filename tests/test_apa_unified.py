"""Exercise the user entry point with real local DXF, IFC, PDF and dump bytes."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import ezdxf
import pymupdf

import apa
from apa_external_ifc_vendor_smoke import create_ifc
from test_apa_ac29_mass_request import request


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class UnifiedAcceptance(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="apa-unified-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)

    def invoke(self, *arguments, code=0):
        result = subprocess.run([sys.executable, "-X", "utf8", "-m", "apa", *map(str, arguments)],
                                cwd=apa.ROOT, capture_output=True, encoding="utf-8", timeout=90)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stderr if code and not result.stdout else result.stdout)

    def save(self, filename, value):
        path = self.work / filename
        apa.write_json(path, value)
        return path

    def test_dxf_preflight_layer_and_block_reports_read_back(self):
        source = self.work / "Разрез.dxf"
        drawing = ezdxf.new("R2018", units=6)
        drawing.blocks.new("Module").add_line((0, 0), (1, 0))
        drawing.modelspace().add_blockref("Module", (2, 3))
        drawing.saveas(source)
        before = digest(source)
        out = self.work / "dxf"
        report = self.invoke("exchange", source, "--output", out)
        self.assertEqual(report["status"], "LOCAL_EXCHANGE_VERIFIED")
        self.assertEqual(report, apa.read_json(out / "report.json"))
        self.assertEqual(report["preflight"]["artifact"]["sha256"], digest(out / "preflight.json"))
        blocks = apa.read_json(out / "DXFBlockInsertions.json")
        self.assertEqual(blocks["result"]["insertions"]["total"], 1)
        self.assertEqual(blocks["sources"][0]["sha256"], before)
        self.assertEqual(digest(source), before)

    def test_ifc_extraction_feeds_vendor_glb_using_graph_result_binding(self):
        source = self.work / "Модель.ifc"
        guid = create_ifc(source, "Unified wall")
        before = digest(source)
        subset = self.work / "subset"
        geometry = self.work / "geometry"
        steps = [
            {"id": "selection", "command": "AddOn.APAIFCArtifactsB2.IFCExtractElements",
             "params": {"a": str(source), "output": str(subset), "query": "IfcWall"}},
            {"id": "mesh", "command": "AddOn.APAIFCGeometryB3.IFCGeometryGLB",
             "params": {"a": {"$result": {"step": "selection", "pointer": "/artifactPath"}},
                        "output": str(geometry), "query": "IfcWall"}},
        ]
        graph = self.save("graph.json", {"operations": list(reversed(steps))})
        receipt = self.work / "workflow.json"
        result = self.invoke("run-read-workflow", "--graph", graph, "--output", receipt)
        self.assertEqual([step["id"] for step in result["trace"]], ["selection", "mesh"])
        self.assertEqual(result["results"]["selection"]["result"]["selectedGlobalIds"], [guid])
        self.assertEqual(result["results"]["mesh"]["source"]["sha256"], digest(subset / "subset.ifc"))
        self.assertEqual(result["results"]["mesh"]["artifact"]["sha256"], digest(geometry / "model.glb"))
        self.assertEqual((geometry / "model.glb").read_bytes()[:4], b"glTF")
        self.assertEqual(apa.read_json(receipt), result)
        self.assertEqual(digest(source), before)

    def test_pdf_vectors_and_page_image_keep_source_units_and_hash(self):
        source = self.work / "Лист.pdf"
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=200, height=200)
            page.draw_line((10, 10), (100, 100))
            pdf.save(source)
        before = digest(source)
        out = self.work / "pdf"
        report = self.invoke("exchange", source, "--output", out)
        self.assertEqual(report["nativeCalls"], 0)
        image = apa.read_json(out / "PDFPageRaster.json")["result"]
        self.assertEqual(image["imageSHA256"], digest(out / "PDFPageRaster.png"))
        self.assertEqual(image["imageSizePx"], [400, 400])
        self.assertEqual(image["modelRealWorldScale"], "NOT_VERIFIED")
        self.assertEqual(digest(source), before)

    def test_pdf_plan_crop_feeds_ap2_hosted_candidates_without_native_authority(self):
        source = self.work / "Этаж.pdf"
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=200, height=200)
            page.insert_text((20, 30), "OK-3")
            page.insert_text((50, 60), "OK-3")
            page.insert_text((160, 160), "OK-3")
            pdf.save(source)
        folder = self.work / "crop"
        candidates = self.work / "candidates.json"
        common = {"a": str(source), "page": 1, "clip": [10, 10, 130, 130]}
        graph = self.save("floorplan.json", {"operations": [
            {"id": "crop", "command": "AddOn.APAArchitecturalSources.PDFPlanCrop",
             "params": {**common, "output": str(folder)}},
            {"id": "candidates", "command": "AddOn.APAArchitecturalSources.HostedOpeningCandidates",
             "params": {**common, "output": str(candidates),
                        "cropReceipt": {"$result": {"step": "crop", "pointer": "/outputEvidence"}},
                        "sourceSha256": {"$result": {"step": "crop", "pointer": "/sourceSHA256"}}}},
        ]})
        result = self.invoke("run-read-workflow", "--graph", graph,
                             "--output", self.work / "plan-workflow.json")
        crop = apa.read_json(folder / "evidence.json")
        self.assertEqual(crop["rasterSHA256"], digest(folder / "floorplan.png"))
        preview = result["results"]["candidates"]
        self.assertEqual(preview, apa.read_json(candidates))
        self.assertEqual(preview["markCounts"], {"ОК-3": 2})
        self.assertIsNone(preview["candidateBatches"][0]["nativeOperationChosen"])
        self.assertFalse(preview["readyForModelWrite"])
        self.assertEqual(preview["sourceSHA256"], digest(source))

    def test_architecture_and_mass_intents_share_existing_scene_writer_routes(self):
        source = apa.ROOT / "examples/accelerator/building-shell.intent.json"
        shell = self.invoke("plan", "--intent", source, "--output", self.work / "shell.json")
        self.assertEqual(shell["status"], "ACCELERATOR_COMPILED_OFFLINE")
        self.assertEqual(shell["inputSha256"], digest(source))
        self.assertEqual({route["executor"] for route in shell["routes"].values()}, {"SceneWriter"})
        self.assertFalse(shell["executionPermission"])
        mass_source = self.save("mass.json", request())
        mass = self.invoke("plan", "--intent", mass_source, "--output", self.work / "mass-plan.json")
        self.assertEqual(mass["placementMode"], "GRID")
        self.assertFalse(mass["executionPermission"])
        self.assertEqual(mass["status"], "GROUP_WORKFLOW_REQUIRES_FRESH_RUNTIME_REGISTRATION")
        self.assertIsNone(mass["selectedNativeTaskPreview"])
        steps = mass["candidateNativeTaskPreview"]["workflow"]["graph"]["operations"]
        self.assertEqual([op["command"] for op in steps], ["AddOn.TapirCommand.CloneNativeGroupV1"])
        self.assertEqual(len(steps[0]["params"]["translations"]), 32)

    def test_arena_terminal_ack_binds_only_an_explicit_typed_input(self):
        receipt = self.save("arena.json", {"protocol": 1, "kind": "terminal_ack", "turn_id": 87,
            "ack_verified": True, "signal_status": "done", "signal_target": "NONE",
            "signal_blob_sha": "a" * 40, "report_marker": "fixture"})
        source = apa.ROOT / "examples/accelerator/r03-gpt-shell-e2e.intent.json"
        output = self.work / "arena-plan.json"
        result = self.invoke("arena-receipt", "--receipt", receipt, "--intent", source, "--output", output)
        self.assertEqual(result["status"], "ARENA_APA_PLAN_PREPARED")
        self.assertEqual(result["receiptSha256"], digest(receipt))
        self.assertEqual(result["intentSha256"], digest(source))
        self.assertEqual(result["plan"]["metrics"]["elementCount"], 10)
        self.assertFalse(result["executionPermission"])
        self.assertFalse(result["plan"]["executionPermission"])
        self.assertEqual(result, apa.read_json(output))

    def test_tdk_trace_delta_compiles_with_scene_writer_and_exact_wall_guid(self):
        from types import SimpleNamespace
        from apa_tdk_wall import trace_candidate

        name = "AI_SOURCE_PACK"
        wall, prop = "11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"
        runtime = SimpleNamespace(trace_values=lambda *_: {name: "pack-02"}, properties={
            name: dict(propertyId={"guid": prop}, propertyName=name, propertyGroupName="AI_TRACE",
                       propertyCollectionType="Single", propertyValueType="String", propertyIsEditable=True)
        })
        decision = dict(status="WOULD_UPDATE_TRACE", dryRun=True, guid=wall,
                        traceDelta={name: {"actual": "pack-01", "desired": "pack-02"}})
        router = apa.load_router()
        result = trace_candidate(router, runtime, {}, "unused-fixture", decision)
        self.assertEqual(result["executor"], "SceneWriter")
        self.assertFalse(result["executionPermission"])
        operation, = result["workflow"]["graph"]["operations"]
        self.assertEqual(operation["command"], "SetPropertyValuesOfElements")
        self.assertEqual(operation["params"]["elementPropertyValues"],
                         [dict(elementId={"guid": wall}, propertyId={"guid": prop},
                               propertyValue={"value": "pack-02"})])
        runtime.properties[name]["propertyGroupName"] = "Another group"
        with self.assertRaisesRegex(ValueError, "TRACE_PROPERTY_DEFINITION_DRIFT"):
            trace_candidate(router, runtime, {}, "unused-fixture", decision)

    def test_native_dump_generates_same_revision_documentation_and_csv(self):
        sample = apa.ROOT / "examples/model_dump_v1.sample.json"
        ids = [e["guid"] for e in apa.read_json(sample)["elements"]]
        selected = self.save("guids.json", ids)
        out = self.work / "documents"
        proof = self.invoke("documentation", "--native-dump", sample, "--guids", selected,
                            "--story", 0, "--output", out)
        package = apa.read_json(out / "documentation.json")
        self.assertEqual(package["modelVersion"], proof["modelVersion"])
        self.assertEqual(proof["sourceSha256"], digest(sample))
        self.assertTrue(proof["sampleOnly"])
        self.assertEqual(proof["artifact"]["sha256"], digest(out / "documentation.json"))
        self.assertEqual(proof["specifications"], {"Morph": 1})
        self.assertIn(proof["modelVersion"], (out / "Morph.csv").read_text(encoding="utf-8-sig"))

    def test_graph_rejects_native_dispatch_before_first_local_artifact(self):
        graph = self.save("invalid.json", {"operations": [
            {"id": "local", "command": "AddOn.APASemantic.PDFPaths",
             "params": {"a": "missing.pdf", "output": str(self.work / "local.json"), "page": 1}},
            {"id": "native", "command": "GetStories", "params": {}},
        ]})
        response = self.invoke("run-read-workflow", "--graph", graph,
                               "--output", self.work / "receipt.json", code=2)
        self.assertEqual(response["reason"], "APA_LOCAL_READ_COMMAND_REQUIRED:GetStories")
        self.assertFalse((self.work / "local.json").exists())
        self.assertFalse((self.work / "receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
