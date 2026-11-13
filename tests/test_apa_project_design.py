from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apa_project_design as design
import archicad_project_accelerator as core
from test_archicad_isolated_authored_execution import IsolatedNative


INPUT = ROOT / "examples/accelerator/r04-project-design.json"


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.input = json.loads(INPUT.read_text(encoding="utf-8"))

    def test_explicit_entrance_stays_linked_and_gross_area_remains_unknown(self):
        first, second = design.compile_design(self.input)["variants"]
        self.assertEqual(first["status"], "DESIGN_CHECKS_REVIEWABLE")
        candidate = first["candidate"]
        self.assertEqual(candidate["plannedNativeCommands"],
                         {"CreateSlabs": 1, "CreateWalls": 5, "CreateDoors": 2, "CreateWindows": 1})
        evidence = {row["id"]: row for row in candidate["requirements"]}
        self.assertEqual(evidence["front-door"]["bimOperationIds"], ["native-opening-entry-door"])
        self.assertEqual(evidence["front-door"]["sourceRef"], "Исходное задание §1")
        self.assertEqual(evidence["gross-area"]["status"], "UNVERIFIED")
        self.assertIsNone(evidence["gross-area"]["measurement"]["valueM2"])
        self.assertEqual(candidate["areaMeasures"]["ROOM_RECTANGLE_SUM"]["valueM2"], 48)
        self.assertEqual(candidate["storyBindings"], [])
        self.assertFalse(candidate["liveWriteAuthorized"])
        self.assertEqual(second["candidate"]["requiredOpenIds"], ["front-door"])

    def test_comparable_areas_and_missing_stair_cannot_be_promoted(self):
        brief = self.input["brief"]
        gross = brief["constraints"][-1]
        gross["criterion"].update(metric="ROOM_RECTANGLE_SUM", targetM2=43)
        gross["priority"] = "REQUIRED"
        brief["stories"].append(dict(id="level-2", label="2 этаж", level=3))
        brief["constraints"].append(dict(id="stairs", text="Межэтажная лестница",
            priority="REQUIRED", sourceRef="ТЗ §4", evidenceStatus="UNVERIFIED",
            criterion=dict(kind="STAIR_LINK", lowerStoryId="level-1", upperStoryId="level-2")))
        for variant in self.input["variants"]:
            variant["storyHeights"]["level-2"] = 3
        self.input["cseCandidate"]["storyIds"].append("level-2")
        candidate = design.compile_design(self.input)["variants"][0]["candidate"]
        facts = {row["id"]: row for row in candidate["requirements"]}
        self.assertEqual(facts["gross-area"]["status"], "CONFLICT")
        self.assertEqual(facts["gross-area"]["deltaM2"], 5)
        self.assertEqual(facts["stairs"]["status"], "MISSING")
        self.assertEqual(set(candidate["requiredOpenIds"]), {"gross-area", "stairs"})

    def test_wrong_room_on_entrance_is_rejected_and_other_variant_is_kept(self):
        self.input["variants"][0]["layout"]["passages"][0]["connects"] = ["$outside", "living"]
        first, second = design.compile_design(self.input)["variants"]
        self.assertEqual(first["status"], "INVALID_VARIANT")
        self.assertEqual(first["reason"], "DOOR_DOES_NOT_CROSS_DECLARED_ROOM_BOUNDARIES")
        self.assertEqual(second["status"], "REQUIREMENTS_OPEN")

    def test_change_tracks_opening_host_and_documents(self):
        changed = deepcopy(self.input)
        row = changed["variants"][0]["layout"]
        row["rooms"][0]["rectangle"]["xMax"] = 3.5
        row["rooms"][1]["rectangle"]["xMin"] = 3.5
        row["axes"][1]["coordinate"] = 3.5
        impact = design.changes_between(self.input, changed, "variant-a")
        self.assertIn("room:hall", impact["changed"])
        self.assertIn("bim:native-opening-hall-door", impact["affected"])
        self.assertIn("requirement:hall-living", impact["affected"])
        self.assertIn("review:sections", impact["affected"])

    def test_selected_variant_uses_original_writer_and_native_readback_ids(self):
        for drift in (False, True):
            with self.subTest(final_door_readback_drift=drift), tempfile.TemporaryDirectory() as folder:
                data = deepcopy(self.input)
                brief = data["brief"]
                path = core.RUN.APPROVED_ISOLATED_WRITER_PATH
                brief.update(mode="ADAPT_EXISTING", targetProjectPath=path)
                brief["stories"][0]["existingNativeLabel"] = "Первый Этаж"
                with self.assertRaisesRegex(ValueError, "REQUIRED_CHECKS_OPEN"):
                    design.select_variant(data, "variant-b")
                intent = design.select_variant(data, "variant-a")
                native = IsolatedNative()
                inventories = 0
                root = Path(folder)
                ledger = root / "ledger"
                ledger.mkdir()

                def transport(command, params):
                    nonlocal inventories
                    observed = native(command, params)
                    if command == "GetAllElements" and len(native.created) == 9:
                        inventories += 1
                    if drift and command == "GetDetailsOfElements" and inventories:
                        guid = params["elements"][0]["elementId"]["guid"]
                        kind, source = native.created[guid]
                        if kind == "CreateDoors" and source["doorsData"][0]["width"] == 1.0:
                            observed["detailsOfElements"][0]["details"]["width"] = 1.25
                    return observed

                with (patch.object(core.RUN, "EXPECTED_PATH", path),
                      patch.object(core.RUN, "EXPECTED_NAME", "APA_Isolated_Writer_Test_01")):
                    args = (intent, core.RUN.DEFAULT_SCENE_SCHEMA)
                    plan = core.run_project(*args, root / "plan", ledger, "preflight", transport)
                    self.assertEqual(plan["status"], "READY_FOR_EXPLICIT_TEST_RUN", plan)
                    result = core.run_project(*args, root / "run", ledger, "execute", transport,
                                              "r04-unit-test", plan["confirmPlanHash"])
                feedback = {row["requirementId"]: row for row in result["requirementReadback"]}
                self.assertEqual(len(result["addedGuids"]), 9, result)
                if drift:
                    self.assertEqual(result["status"], "PARTIAL_OR_UNKNOWN_OUTCOME", result)
                    self.assertEqual(feedback["front-door"]["nativeReadback"], "MISMATCH")
                else:
                    self.assertEqual(result["status"], "COMPLETE_UNSAVED", result)
                    self.assertEqual(feedback["front-door"]["nativeReadback"], "LINKED_ELEMENTS_READ_BACK")
                self.assertIn(feedback["front-door"]["operations"]["native-opening-entry-door"]["guid"],
                              result["addedGuids"])

    def test_cli_reads_utf8_request_without_claiming_interpretation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, result = root / "request.txt", root / "result.json"
            source.write_text("Нужен вход из холла в гостиную.", encoding="utf-8")
            process = subprocess.run([sys.executable, "-B", "-X", "utf8", "-m", "apa",
                                      "design-request", "--source", source, "--output", result],
                                     cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=40)
            self.assertEqual(process.returncode, 0, process.stderr)
            document = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(document["status"], "GPT_INTERPRETATION_REQUIRED")
            self.assertEqual(document["sourceText"], source.read_text(encoding="utf-8"))
            self.assertFalse(document["executionPermission"])
