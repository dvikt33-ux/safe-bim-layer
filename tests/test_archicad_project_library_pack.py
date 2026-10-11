"""Project library pack: offline CSE selection with real project attribute read-only."""
from pathlib import Path
import copy
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

import archicad_project_accelerator as A
from test_archicad_semantic_brief import valid, SyntheticStories

BM="Железобетон - Конструкционный"
BM_GUID="63db2ce9-903d-45c0-b93c-b3c604c77394"
SOURCE_SHA="e4bf711bdc3322f594699b59ea34107cde0bcfdf"
SOURCE_URL=("https://github.com/dvikt33-ux/safe-bim-layer/blob/"
  "research/apa-verified-results-hub-20261010/docs/research/apa-results/"
  "runs/2026-10-11/apa-p70-a03-s02-pr35-basic-slab-implementation-partial-20261011.md")


def specimen():
    return {
      "candidateId":"rc-basic-slab-v1",
      "systemFamily":"reinforced-concrete-slab-provisional",
      "role":"floor-slab",
      "source":{
        "sourceId":"apa-native-slab-readback-20261011",
        "uri":SOURCE_URL,"gitBlobSha":SOURCE_SHA,
        "publisher":"APA user-supplied native readback",
        "rights":"LINK_ONLY_RIGHTS_UNVERIFIED",
        "status":"PROJECT_NATIVE_READBACK",
        "licenseEvidenceUri":None,
        "applicabilityNote":"Only existing disposable PLN Basic Slab source; structural design not assessed",
      },
      "native":{"attributeType":"BuildingMaterial","name":BM,
                "expectedProjectGuid":BM_GUID},
      "thicknessMeters":.2,
      "storyIds":["level-1","level-2"],
      "requiredInterfaceConditions":[
        "slab-wall-bearing","floor-waterproofing","slab-opening-penetration"],
      "selectedDetailIds":[],
    }


class NativeGetOnly(SyntheticStories):
    def __init__(self, names=None):
        super().__init__()
        self.names=names or [BM]
    def __call__(self,cmd,args):
        if cmd=="GetAttributesByType":
            self.calls.append(cmd)
            self._assert_attribute_type(args)
            return {"attributes":[{"name":x,"attributeId":{"guid":BM_GUID}}
                                  for x in self.names]}
        return super().__call__(cmd,args)
    @staticmethod
    def _assert_attribute_type(args):
        if args!={"attributeType":"BuildingMaterial"}:
            raise AssertionError("wrong native attributes request")


class ProjectLibraryPackTests(unittest.TestCase):
    def test_new_project_offline_not_native_approved(self):
        a=A.compile_project_library_pack(valid("GENERATE_FROM_ZERO"),specimen())
        self.assertEqual(a["schemaVersion"],"apa-project-library-pack/1")
        self.assertEqual(a["projectMode"],"GENERATE_FROM_ZERO")
        self.assertEqual(a["selectedCseCandidates"][0]["native"]["guid"],None)
        self.assertEqual(a["status"],"PROVISIONAL_CSE_AWAITING_NATIVE_BINDING")
        self.assertFalse(a["selectedCseCandidates"][0]["engineeringApproved"])
        self.assertEqual(len(a["missingCriticalConditionIds"]),3)
        self.assertEqual(a["nativeWriteCalls"],0)

    def test_existing_project_matches_actual_story_and_native_material(self):
        native=NativeGetOnly()
        out=A.compile_project_library_pack(valid(),specimen(),native)
        self.assertEqual(out["status"],"PROJECT_NATIVE_MATERIAL_RESOLVED_NOT_ENGINEER_APPROVED")
        self.assertEqual(out["selectedCseCandidates"][0]["native"]["guid"],BM_GUID)
        self.assertEqual([x["nativeIndex"] for x in out["nativeStoryBindings"]],[1,3])
        self.assertEqual(native.calls,[
            "GetProjectInfo","GetStories","GetProjectInfo",
            "GetAttributesByType","GetProjectInfo"])
        self.assertEqual(out["missingCriticalConditionIds"],
                         specimen()["requiredInterfaceConditions"])
        self.assertFalse(out["selectedCseCandidates"][0]["detailApproved"])
        self.assertFalse(out["selectedCseCandidates"][0]["engineeringApproved"])
        self.assertEqual(out["importedLibraryObjects"],[])
        self.assertEqual(out["nativeWriteCalls"],0)

    def test_reuse_exact_previous_native_floor_material_resolver(self):
        import archicad_project_library_pack as PLP
        self.assertIsNotNone(PLP.RUN.resolve_basic_slab_material)
        self.assertIs(PLP.RUN.resolve_basic_slab_material,
                      A.RUN.resolve_basic_slab_material)

    def test_no_native_matches_must_fail_closed(self):
        native=NativeGetOnly(["Другой материал"])
        with self.assertRaisesRegex(ValueError,"BASIC_SLAB_MATERIAL_MISSING_OR_AMBIGUOUS"):
            A.compile_project_library_pack(valid(),specimen(),native)

    def test_duplicate_material_names_must_fail_closed(self):
        native=NativeGetOnly([BM,BM])
        with self.assertRaisesRegex(ValueError,"BASIC_SLAB_MATERIAL_MISSING_OR_AMBIGUOUS"):
            A.compile_project_library_pack(valid(),specimen(),native)

    def test_unexpected_native_guid_cannot_be_substituted(self):
        c=specimen()
        c["native"]["expectedProjectGuid"]="11111111-1111-4111-8111-111111111111"
        with self.assertRaisesRegex(ValueError,"PROJECT_BUILDING_MATERIAL_GUID_CHANGED"):
            A.compile_project_library_pack(valid(),c,NativeGetOnly())

    def test_reject_unknown_source_license_and_self_approval(self):
        c=specimen()
        c["source"]["rights"]="LICENSE_SOURCE_VERIFIED"
        with self.assertRaisesRegex(ValueError,"CSE_LICENSE_OR_EVIDENCE_STATUS_INVALID"):
            A.compile_project_library_pack(valid(),c)
        c=specimen()
        c["selectedDetailIds"]=["UNAPPROVED_DETAIL_00001"]
        with self.assertRaisesRegex(ValueError,"DETAIL_BINDINGS_REQUIRE_INDEPENDENT"):
            A.compile_project_library_pack(valid(),c)

    def test_reject_wrong_live_file_without_attribute_inventory(self):
        native=NativeGetOnly()
        def wrong(cmd,params):
            x=native(cmd,params)
            if cmd=="GetProjectInfo":
                x["projectPath"]=r"C:\wrong\other.pln"
            return x
        with self.assertRaisesRegex(ValueError,"WRONG_ACTIVE_SINGLE_PLN"):
            A.compile_project_library_pack(valid(),specimen(),wrong)
        self.assertEqual(native.calls,["GetProjectInfo"])

    def test_never_accepts_missing_story(self):
        native=NativeGetOnly()
        native.names=("Elsewhere","Not used")
        # Duplicate/unknown native BM always fails; first ensure story conflict gate.
        wrong=NativeGetOnly()
        wrong.names=[BM]
        def story_drift(cmd,params):
            res=wrong(cmd,params)
            if cmd=="GetStories":
                res["stories"][0]["name"]="unknown-story"
            return res
        res=A.compile_project_library_pack(valid(),specimen(),story_drift)
        self.assertEqual(res["status"],"NEEDS_STORY_RESOLUTION")
        self.assertNotIn("nativeStoryBindings",res)
        self.assertEqual(wrong.calls,["GetProjectInfo","GetStories"])

    def test_reject_duplicate_conditions_and_unknown_story_id(self):
        c=specimen()
        c["requiredInterfaceConditions"].append(c["requiredInterfaceConditions"][0])
        with self.assertRaisesRegex(ValueError,"CSE_REQUIRED_INTERFACE"):
            A.compile_project_library_pack(valid(),c)
        c=specimen()
        c["storyIds"]=["level-unlisted"]
        with self.assertRaisesRegex(ValueError,"CSE_STORY_SCOPE"):
            A.compile_project_library_pack(valid(),c)

    def test_reject_unpinned_source_and_unspecified_thickness(self):
        c=specimen()
        c["source"]["gitBlobSha"]=None
        with self.assertRaisesRegex(ValueError,"SOURCE_BLOB_SHA"):
            A.compile_project_library_pack(valid(),c)
        c=specimen();c["thicknessMeters"]=float("nan")
        with self.assertRaisesRegex(ValueError,"CSE_THICKNESS"):
            A.compile_project_library_pack(valid(),c)
        c=specimen();c["source"]["uri"]="https://example.com/unreviewed"
        with self.assertRaisesRegex(ValueError,"UNPINNED_OR_EXTERNAL"):
            A.compile_project_library_pack(valid(),c)

    def test_constraint_norm_status_keeps_pending(self):
        source=valid()
        self.assertEqual(source["constraints"][0]["evidenceStatus"],"UNVERIFIED")
        result=A.compile_project_library_pack(source,specimen())
        self.assertIsNone(result["normativePackDigest"])
        self.assertTrue(result["missingCriticalConditionIds"])
        self.assertEqual(result["licenseAndStoragePermission"],"NO_EXTERNAL_FILES_IMPORTED")


if __name__=="__main__":
    unittest.main()
