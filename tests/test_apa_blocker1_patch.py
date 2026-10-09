from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "docs" / "research" / "patches" / "tapir-1.5.10-blocker1-readonly-diagnostic.patch"


class Blocker1PatchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = PATCH.read_text(encoding="utf-8")

    def test_native_resolver_uses_exact_createobjects_search_flags(self):
        self.assertIn("libraryPartName.GetLength () >= API_UniLongNameLen", self.patch)
        self.assertIn("ACAPI_LibraryPart_Search (&probe, false, true)", self.patch)
        self.assertIn("GS::ucscpy (probe.docu_UName, libraryPartName.ToUStr ())", self.patch)
        self.assertIn('"libraryPartName"', self.patch)

    def test_returns_all_requested_api29_libpart_fields(self):
        for field in ("err", "index", "ownUnID", "parentUnID", "docu_UName", "file_UName", "isPlaceable", "missingDef", "typeID"):
            self.assertRegex(self.patch, rf'\"{re.escape(field)}\"')

    def test_inventory_has_full_skipped_index_error_list_without_truncation(self):
        self.assertIn("ACAPI_LibraryPart_GetNum (&partCount)", self.patch)
        self.assertIn("for (Int32 i = 1; i <= partCount; ++i)", self.patch)
        self.assertIn("ACAPI_LibraryPart_Get (&item)", self.patch)
        self.assertIn('AddList<GS::ObjectState> ("skippedIndices")', self.patch)
        self.assertIn('skipped.Add ("index", i)', self.patch)
        self.assertIn('skipped.Add ("error", static_cast<Int32> (getErr))', self.patch)
        self.assertIn('response.Add ("inventory", inventory)', self.patch)
        self.assertIn("return response;", self.patch)
        self.assertNotIn("maxSkipped", self.patch)

    def test_patch_does_not_call_any_mutating_api(self):
        forbidden = (
            "ACAPI_Element_Create", "ACAPI_Element_Change", "ACAPI_Element_Delete",
            "ACAPI_LibPart_Set", "ACAPI_LibPart_Create", "ACAPI_ProjectOperation_Save",
            "ACAPI_ProjectOperation_ReloadLibraries", "ACAPI_Environment (APIEnv_SetLibrariesID",
        )
        for token in forbidden:
            self.assertNotIn(token, self.patch)


if __name__ == "__main__":
    unittest.main()
