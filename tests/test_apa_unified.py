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
