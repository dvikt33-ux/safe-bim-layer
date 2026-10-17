"""Focused checks ONLY for the NEW reusable copy/reconciliation contracts."""
import json
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_reusable_native_copy as COPY
import apa_ac29_scene_reconciliation as RECON

SOURCE = "b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"


def manifest():
    return dict(schemaVersion="apa-ac29-native-column-copy/1",
                projectSha256="a"*64,projectPath="C:\\Projects\\approved.pln",
                prototypeGuid=SOURCE,prototypeOrigin={"x":1.5,"y":2.5},
                targets=[{"x":3.5,"y":2.5},{"x":4.5,"y":2.5}],
                sceneId="COPY_APPROVED_001",saveSceneId="SAVE_APPROVED_001",
                authorizationRef="USER_APPROVED_EXACT_NATIVE_COPIES",
                sourceEvidenceRef="https://github.com/owner/repo/blob/commit/manifest",
                save=True)


class NativeCopyContracts(unittest.TestCase):
    def test_two_source_qualified_targets(self):
        m=manifest()
        self.assertIs(COPY.validate_task(m,expected_project_sha="a"*64,
                    expected_project_path="C:\\Projects\\approved.pln"),m)

    def test_cannot_write_unapproved_project(self):
        with self.assertRaisesRegex(ValueError,"APPROVED_PLN"):
            COPY.validate_task(manifest(),expected_project_sha="b"*64,
                               expected_project_path="C:\\Projects\\approved.pln")

    def test_no_duplicate_target_or_no_save(self):
        m=manifest();m["targets"].append(dict(m["targets"][0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            COPY.validate_task(m,expected_project_sha="a"*64,
                               expected_project_path=m["projectPath"])
        m=manifest();m["save"]=False
        with self.assertRaisesRegex(ValueError,"APPROVAL"):
            COPY.validate_task(m,expected_project_sha="a"*64,
                               expected_project_path=m["projectPath"])

    def test_reused_scene_requires_distinct_scene_ids(self):
        m=manifest();m["saveSceneId"]=m["sceneId"]
        with self.assertRaisesRegex(ValueError,"SCENE_MUST_DIFFER"):
            COPY.validate_task(m,expected_project_sha="a"*64,
                               expected_project_path=m["projectPath"])

    def test_translated_body_uses_shape_not_assumed_rectangle(self):
        row={"bodies":[{"vertices":[[3,4,0],[3.1,4,0],[3.1,4.05,2.9]]}]}
        first=COPY.translated_vertices(row,{"x":3,"y":4})
        moved={"bodies":[{"vertices":[[9,8,0],[9.1,8,0],[9.1,8.05,2.9]]}]}
        second=COPY.translated_vertices(moved,{"x":9,"y":8})
        self.assertEqual(first,second)

    def test_guid_roots_are_classified_from_brep_not_get_all_elements(self):
        result={"elements":[{"guid":SOURCE,"type":"Column","bodies":[]}]}
        mapping=COPY.native_map(result,lambda m:m)
        self.assertEqual(mapping[SOURCE]["type"],"Column")

    def test_old_unknown_must_not_be_reused_as_pass(self):
        records=[{"command":"GetAllElements","response":{"elements":[]}},
                 {"command":"GetModelDumpV1","response":{"elements":[]}},
                 {"command":"MoveElements","response":{"executionResults":[{"success":True}]}}]
        inv,model,index=RECON.snapshot_before_dispatch(records)
        self.assertEqual(index,2)
        self.assertEqual(model["elements"],[])

    def test_no_baseline_no_reconciliation(self):
        with self.assertRaisesRegex(ValueError,"PREWRITE_NATIVE_BASELINE"):
            RECON.snapshot_before_dispatch([
                {"command":"MoveElements","response":{"executionResults":[{"success":True}]}}
            ])

    def test_history_comparison_does_not_mutate_sqlite(self):
        with TemporaryDirectory() as temp:
            folder=Path(temp)
            journal=folder/"state.sqlite"
            con=sqlite3.connect(journal)
            con.execute("CREATE TABLE scenes (scene_id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)")
            con.execute("CREATE TABLE steps (scene_id TEXT,step_id TEXT,state TEXT,guid TEXT,output TEXT,PRIMARY KEY(scene_id,step_id))")
            con.execute("INSERT INTO scenes VALUES(?,?,?,?)",
                        ("HISTORIC_NATIVE_COPY","abc","PARTIAL_OR_UNKNOWN_OUTCOME",
                         json.dumps({"reason":"postwrite verifier failed"})))
            con.execute("INSERT INTO steps VALUES(?,?,?,?,?)",
                        ("HISTORIC_NATIVE_COPY","operation","UNKNOWN_OUTCOME",None,"{}"))
            con.commit();con.close()
            native={"elements":[{"guid":SOURCE,"type":"Column","bodies":[]}]}
            inventory={"elements":[{"elementId":{"guid":SOURCE}}]}
            records=[{"command":"GetAllElements","response":inventory},
                     {"command":"GetModelDumpV1","response":native},
                     {"command":"MoveElements","response":{"executionResults":[{"success":True}]}}]
            raw=folder/"raw.jsonl"
            raw.write_text("\n".join(json.dumps(r) for r in records)+"\n")
            class Fake:
                write_attempts=0
                def __call__(self,command,p):
                    return inventory if command=="GetAllElements" else native
            digest=lambda value:json.dumps(value,sort_keys=True)
            proof=RECON.read_only_reconciliation(
                "HISTORIC_NATIVE_COPY",journal,raw,Fake(),
                normalized=lambda row:row,geom_signature=lambda row:row["type"],
                digest=digest,expected_project_sha="abc",
                current_project_sha="abc")
            self.assertEqual(proof["liveGuidCount"],1)
            self.assertTrue(proof["originalUnknownRowsPreserved"])
            with sqlite3.connect(journal) as db:
                self.assertEqual(db.execute("SELECT state FROM scenes").fetchone()[0],
                                 "PARTIAL_OR_UNKNOWN_OUTCOME")

    def test_live_brep_drift_refuses_historical_clearance(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)
            journal=path/"state.sqlite"
            db=sqlite3.connect(journal)
            db.execute("CREATE TABLE scenes (scene_id TEXT PRIMARY KEY, state TEXT, result TEXT)")
            db.execute("CREATE TABLE steps (scene_id TEXT, state TEXT)")
            db.execute("INSERT INTO scenes VALUES (?,?,?)",
                       ("HISTORIC_NATIVE_COPY","PARTIAL_OR_UNKNOWN_OUTCOME","{}"))
            db.execute("INSERT INTO steps VALUES (?,?)",
                       ("HISTORIC_NATIVE_COPY","UNKNOWN_OUTCOME"))
            db.commit();db.close()
            original={"elements":[{"guid":SOURCE,"type":"Column","bodies":[]}]}
            current={"elements":[{"guid":SOURCE,"type":"Column","bodies":[{"vertices":[[1,2,3]]}]}]}
            inv={"elements":[{"elementId":{"guid":SOURCE}}]}
            raw=path/"events.jsonl"
            raw.write_text("\n".join(map(json.dumps,[
                {"command":"GetAllElements","response":inv},
                {"command":"GetModelDumpV1","response":original},
                {"command":"MoveElements","response":{"executionResults":[{"success":True}]}}
            ])))
            class Fake:
                write_attempts=0
                def __call__(self,name,_):
                    return inv if name=="GetAllElements" else current
            with self.assertRaisesRegex(ValueError,"BREP_NOT_EQUAL"):
                RECON.read_only_reconciliation(
                    "HISTORIC_NATIVE_COPY",journal,raw,Fake(),
                    normalized=lambda d:d,
                    geom_signature=lambda row:row.get("bodies"),
                    digest=lambda v:"sha",expected_project_sha="abc",
                    current_project_sha="abc")


if __name__=="__main__":
    unittest.main()
