import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_native_contract_gap_report_d1 as D


class InventoryTests(unittest.TestCase):
    def test_existing_repository_contracts_are_not_new_or_live(self):
        root = Path(__file__).resolve().parents[1]
        result = D.inventory(root / "schemas/tapir-live-1.5.10/tapir-scene-live.json",
                             root / "schemas/accelerator/functional-modules.json")
        hotlink = result["areas"]["hotlinks"]
        self.assertIn("CreateHotlinkInstances", [r["command"] for r in hotlink["contracts"]])
        self.assertEqual(result["newCallableNativeCommands"], 0)
        self.assertTrue(all(r["liveRegistration"] == "NOT_PROBED" for r in result["areas"].values()))
        self.assertEqual(result["areas"]["grid_axes"]["gap"], "NO_MATCHING_CONTRACT")

    def test_stale_receipt_is_rejected(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "receipt.json"
            receipt.write_text(json.dumps({"schemaSHA256": "0" * 64}))
            with self.assertRaisesRegex(ValueError, "SCHEMA_RECEIPT_DRIFT"):
                D.inventory(root / "schemas/tapir-live-1.5.10/tapir-scene-live.json",
                            root / "schemas/accelerator/functional-modules.json", receipt)


if __name__ == "__main__":
    unittest.main()
