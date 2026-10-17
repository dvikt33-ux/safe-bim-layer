"""BDD 2026-10-16/17 paired historical UNKNOWN acceptance is read-only.

Synthetic full-size 290->298 native model, SHA-bound SQLite scenes and original
raw-log content. No live Archicad calls or mutation permission.
"""
from collections import Counter
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import copy
import hashlib
import json
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import apa_ac29_scene_reconciliation as R
import apa_ac29_dynamic_write_scopes as S
import archicad_connected_components as C
import archicad_scene_run as RUN


def uid(i):
    return f"{i:08x}-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def native_row(i, kind="Object", parent=None, center=None):
    result={"guid":uid(i),"type":kind,"homeStory":0,
            "materialBindings":{},"relationships":{},
            "bodies":[]}
    if parent is not None:
        result["relationships"]={"hostGuid":uid(parent)}
    if center is not None:
        x,y=center
        result["bodies"]=[{"closed":True,
                          "vertices":[[x-.02,y-.02,0],[x+.02,y+.02,2.9]]}]
    return result


def fixture(root):
    original=[native_row(i) for i in range(1,291)]
    copied=[
        native_row(291,"Column"),
        native_row(292,"Column"),
        native_row(293,"Column"),
        native_row(294,"Beam"),
        native_row(295,"ColumnSegment",291,(155,150)),
        native_row(296,"ColumnSegment",292,(157,150)),
        native_row(297,"ColumnSegment",293,(175,150)),
        native_row(298,"BeamSegment",294,(185,150)),
    ]
    current=original+copied
    before_guids=[row["guid"] for row in original]
    prewrite={
        "elements":[{"elementId":{"guid":g}} for g in before_guids]}
    prewrite_model={"elements":original}
    raw=root/"raw.jsonl"
    rows=[
        {"command":"GetAllElements","response":prewrite},
        {"command":"GetModelDumpV1","response":prewrite_model},
        {"command":"MoveElements","response":{"executionResults":[]}}
    ]
    raw.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf8")
    pending={}
    for scene, (reason, count) in {
        "BDD_BULK150_GRID_AND_LINE_20261016":
            ("MASS_COPY_UNEXPECTED_NATIVE_ELEMENT_TYPES",150),
        "APA_AC29_REMOTE_COLUMN_BEAM_MULTI_COPY_20261017":
            ("MULTI_COPY_NATIVE_ROOT_DETAILS_BREP_NOT_UNIQUE",2),
    }.items():
        raw_result=json.dumps({
            "command":"MoveElements",
            "reason":"ValueError: "+reason,
            "nativeResponse":{"executionResults":[{"success":True}]*count},
        })
        pending[scene]=(raw_result,reason,count)
    ledger=root/"ledger.sqlite"
    with closing(sqlite3.connect(ledger)) as db:
        db.execute("CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,state TEXT,result TEXT)")
        db.execute("CREATE TABLE steps(scene_id TEXT,step_id TEXT,state TEXT)")
        for scene,(value,_,_) in pending.items():
            db.execute("INSERT INTO scenes VALUES(?,?,?)",
                       (scene,"PARTIAL_OR_UNKNOWN_OUTCOME",value))
            db.execute("INSERT INTO steps VALUES(?,?,?)",
                       (scene,"operation","UNKNOWN_OUTCOME"))
        create_proof={
            "status":"NATIVE_COLUMN_CREATE_TYPED_AND_BREP_READBACK_PASS",
            "newRootGuids":[uid(291),uid(292)],
            "newRootCount":2,"newSegmentCount":2,
        }
        db.execute("INSERT INTO scenes VALUES(?,?,?)",(
            "APA_AC29_REMOTE_COLUMNS_CREATE_20261017","PASS",
            json.dumps({"command":"CreateColumns","readback":create_proof})))
        for name,sha in R._BDD_SAVES.items():
            db.execute("INSERT INTO scenes VALUES(?,?,?)",(
                name,"PASS",json.dumps({
                    "command":"SaveProject","readback":{"savedSha256":sha}
                })))
        db.commit()
    known={
        scene:(hashlib.sha256(value.encode()).hexdigest(),reason,count)
        for scene,(value,reason,count) in pending.items()
    }
    return ledger,raw,prewrite_model,current,known


class PairedBddHistory(TestCase):
    def setUp(self):
        self.dir=TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root=Path(self.dir.name)
        (self.ledger,self.raw,self.original,
         self.current,self.known)=fixture(self.root)
        self.first=sorted(row["guid"] for row in self.original)
        prebrep={g:[] for g in self.first}
        self.patches=[
            patch.object(R,"_BDD_HISTORY",self.known),
            patch.object(R,"_BDD_BULK_RAW_SHA",
                         hashlib.sha256(self.raw.read_bytes()).hexdigest()),
            patch.object(R,"_BDD_PREWRITE_GUID_HASH",RUN.digest(self.first)),
            patch.object(R,"_BDD_PREWRITE_BREP_HASH",RUN.digest(prebrep)),
            patch.object(C.G,"normalize_dump",
                         side_effect=lambda raw:self.original_dump(raw)),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.api=SimpleNamespace(write_attempts=0)

    def original_dump(self,raw):
        return copy.deepcopy(raw)

    def reconcile(self,model=None):
        active=copy.deepcopy(model if model is not None else self.current)
        return R.reconcile_bdd_paired_history_read_only(
            self.ledger,self.raw,self.api,
            current_project_sha=R._BDD_SAVED_298_SHA,
            source_project_sha="a"*64,
            expected_source_sha="a"*64,
            guid_inventory=lambda api:[row["guid"] for row in active],
            capture_model=lambda api,ids:{"elements":active},
            geom_signature=C.ROOF.geometry_signature,
            digest=RUN.digest)

    def test_proved_two_historic_scenes_allow_scope_without_rewriting_sqlite(self):
        original_bytes=self.ledger.read_bytes()
        proof=self.reconcile()
        self.assertEqual(proof["status"],
                         "BDD_PAIRED_HISTORY_CURRENT_MODEL_RECONCILED_PASS")
        self.assertEqual(proof["addedGuidCount"],8)
        self.assertEqual(len(proof["historicalProofs"]),2)
        self.assertEqual(proof["modelWrites"],0)
        self.assertEqual(proof["nativeSaveCalls"],0)
        pending=S.validate_existing_ledger(
            self.ledger,"NewAfterHistoricScene",proof)
        self.assertEqual(len(pending),2)
        self.assertEqual(self.ledger.read_bytes(),original_bytes)

    def test_changed_original_result_sha_is_rejected(self):
        proof=self.reconcile()
        with closing(sqlite3.connect(self.ledger)) as db:
            db.execute("UPDATE scenes SET result=? WHERE scene_id=?",
                       ("{}", "BDD_BULK150_GRID_AND_LINE_20261016"))
            db.commit()
        with self.assertRaisesRegex(ValueError,
                                    "PAIRED_HISTORY_ORIGINAL_SQLITE_CHANGED"):
            S.validate_existing_ledger(
                self.ledger,"NewAfterHistoricScene",proof)

    def test_material_or_typed_geometry_drift_is_not_reconciled(self):
        altered=copy.deepcopy(self.current)
        altered[0]["materialBindings"]={
            "buildingMaterial":{"guid":uid(400)}}
        with self.assertRaisesRegex(ValueError,
                                    "ORIGINAL_290_TYPED_BREP_OR_MATERIAL_CHANGED"):
            self.reconcile(altered)

    def test_new_unowned_segment_is_not_explained(self):
        altered=copy.deepcopy(self.current)
        altered[-1]["relationships"]["hostGuid"]=uid(400)
        with self.assertRaisesRegex(ValueError,
                                    "UNEXPLAINED_NATIVE_CHILD_OWNERSHIP"):
            self.reconcile(altered)

    def test_extra_unknown_scene_is_not_silently_accepted(self):
        with closing(sqlite3.connect(self.ledger)) as db:
            db.execute("INSERT INTO scenes VALUES(?,?,?)",
                       ("AnotherUncertainScene","UNKNOWN_OUTCOME","{}"))
            db.commit()
        with self.assertRaisesRegex(ValueError,
                                    "UNEXPECTED_UNRESOLVED_SCENES"):
            self.reconcile()

    def test_previous_scene_id_still_cannot_replay(self):
        proof=self.reconcile()
        with self.assertRaisesRegex(ValueError,
                                    "SCENE_ID_ALREADY_USED_NEVER_RETRY"):
            S.validate_existing_ledger(
                self.ledger,"BDD_BULK150_GRID_AND_LINE_20261016",proof)


if __name__=="__main__":
    from unittest import main
    main()
