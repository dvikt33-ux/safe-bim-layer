"""Only new GitHub bridge authorization, deduplication and ingress checks."""
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import unittest
import json
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_autonomous_job_bridge as bridge


def sample(action="BDD114_ROOF_FINALIZE", name="bdd114-roof-20261017"):
    now = datetime.now(timezone.utc)
    stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": "APA_AC29_AUTONOMOUS_JOB_V1",
        "jobId": name,
        "action": action,
        "createdAt": stamp(now-timedelta(seconds=30)),
        "expiresAt": stamp(now+timedelta(hours=2)),
        "projectSha256": bridge.BASE_SHA,
        "sourceTask": None,
    }


class SixVerifierRuntimeReceipt(TestCase):
    def test_six_verified_modules_are_an_explicit_release_shape(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            controllers=root/"controllers"
            controllers.mkdir()
            base=set(bridge.MODULE_HASHES)|{
                "apa_ac29_dynamic_write_scopes.py",
                "apa_ac29_dynamic_native_verifiers.py",
                "apa_ac29_reusable_native_copy.py",
                "apa_ac29_multi_prototype_native_copy.py",
                "apa_ac29_scene_reconciliation.py",
                "apa_ac29_existing_create_verifiers.py",
                "apa_ac29_existing_modify_verifiers.py",
            }
            helpers={
                "apa_ac29_reusable_native_copy.py",
                "apa_ac29_multi_prototype_native_copy.py",
                "apa_ac29_scene_reconciliation.py",
            }
            receipt={
                "schema":"APA_AC29_RUNTIME_RELEASE_V1",
                "revision":"d"*40,
                "workerSHA256":"a"*64,
                "workingPlnSha256":"b"*64,
                "expectedGuidCount":298,
                "moduleHashes":{name:"c"*64 for name in base},
                "controllerHashes":{name:"e"*64 for name in helpers},
            }
            path=controllers/"runtime-release.json"
            path.write_text(json.dumps(receipt),encoding="utf8")
            with patch.object(bridge,"ROOT",root), \
                 patch.object(bridge,"sha",return_value="a"*64):
                self.assertEqual(bridge.runtime_release()["expectedGuidCount"],298)
                receipt["moduleHashes"]["unknown_new_native_module.py"]="f"*64
                path.write_text(json.dumps(receipt),encoding="utf8")
                with self.assertRaisesRegex(ValueError,
                                            "LOCAL_RUNTIME_RELEASE_RECEIPT_INVALID"):
                    bridge.runtime_release()


class GateTests(TestCase):
    def setUp(self):
        # Unit ingress cases must never consult a real installed deployment.
        deployment=patch.object(bridge,'runtime_release',return_value=None)
        deployment.start();self.addCleanup(deployment.stop)

    def test_model_fingerprint_consumes_existing_normalized_capture_once(self):
        import archicad_project_accelerator as A
        import archicad_bim_documentation as D
        guid='b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c'
        model={'elements':[{'guid':guid,'type':'Object','homeStory':0,
                            'bodies':[],'relationships':{},'materialBindings':{}}]}
        def native(command,parameters):
            if command=='API.GetProductInfo':return {'version':29,'buildNumber':5101}
            if command=='GetAllElements':return {'elements':[{'elementId':{'guid':guid}}]}
            raise AssertionError(command)
        with TemporaryDirectory() as td, \
             patch.object(bridge,'sha',side_effect=lambda p:bridge.SOURCE_SHA if p==bridge.ORIGINAL else bridge.BASE_SHA), \
             patch.object(bridge,'approved_guid_count',return_value=1), \
             patch.object(A.RUN,'bind_authorized_saved_copy'), \
             patch.object(A.RUN,'guarded_project_for_read',return_value={'activeViewStoryIndex':0}), \
             patch.object(A,'native_transport',side_effect=native), \
             patch.object(D,'capture_full_model',return_value=model):
            result=bridge.capture_current_model_fingerprint(sample(),Path(td))
        self.assertEqual(result['expectedGuidCount'],1)
        self.assertEqual(result['nativeWriteAttempts'],0)

    def test_legacy_fixed_bdd_write_is_retired_at_ingress_and_direct_entry(self):
        m=sample('BDD114_COPY_SAVE','bdd114-seven-copy-save-20261017')
        with self.assertRaisesRegex(ValueError,'JOB_ACTION_OR_TARGET_NOT_ALLOWED'):
            bridge.validate_job(m,m['jobId'])
        with patch.object(bridge.subprocess,'run',side_effect=AssertionError('WRITE_DISPATCHED')):
            with self.assertRaisesRegex(ValueError,'LEGACY_BDD_WRITE_RETIRED'):
                bridge.capture_approved_bdd114_copy(m,Path('unused'))

    def test_both_copy_actions_require_exact_local_blob_bound_grant(self):
        for action in ('APPROVED_NATIVE_COLUMN_COPY','APPROVED_MULTI_PROTOTYPE_COPY'):
            with self.subTest(action=action), TemporaryDirectory() as td:
                root=Path(td);(root/'controller-grants').mkdir()
                folder=root/'attempt';folder.mkdir()
                (folder/'attempted.json').write_text(json.dumps({'sourceBlob':'a'*40}),encoding='utf8')
                job=sample(action)
                with patch.object(bridge,'ROOT',root):
                    with self.assertRaisesRegex(ValueError,'LOCAL_EXPLICIT_GRANT_NOT_INSTALLED'):
                        bridge.require_native_copy_grant(job,folder,'b'*40,'USER_APPROVED_STRING_IN_GITHUB')
                    grant={'schema':'APA_AC29_LOCAL_NATIVE_COPY_GRANT_V1','jobId':job['jobId'],
                        'jobBlobSha1':'a'*40,'taskBlobSha1':'b'*40,'projectSha256':bridge.BASE_SHA,
                        'authorizationRef':'USER_APPROVED_LOCAL'}
                    path=root/'controller-grants'/(job['jobId']+'.json')
                    path.write_text(json.dumps(grant),encoding='utf8')
                    self.assertEqual(bridge.require_native_copy_grant(
                        job,folder,'b'*40,'USER_APPROVED_LOCAL'),grant)
                    with self.assertRaisesRegex(ValueError,'NOT_BOUND_TO_JOB_BLOB'):
                        bridge.require_native_copy_grant(job,folder,'c'*40,'USER_APPROVED_LOCAL')
                    with self.assertRaisesRegex(ValueError,'NOT_BOUND_TO_JOB_BLOB'):
                        bridge.require_native_copy_grant(job,folder,'b'*40,'USER_APPROVED_CHANGED')

    def test_source_review_only_job_is_accepted(self):
        m = sample()
        self.assertEqual(bridge.validate_job(m, m["jobId"])["action"],
                         "BDD114_ROOF_FINALIZE")

    def test_no_unreviewed_write_action(self):
        m = sample()
        m["action"] = "CREATE_COLUMNS"
        with self.assertRaisesRegex(ValueError, "JOB_ACTION_OR_TARGET_NOT_ALLOWED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_foreign_pln_hash(self):
        m = sample()
        m["projectSha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "JOB_ACTION_OR_TARGET_NOT_ALLOWED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_unpinned_source_task(self):
        m = sample("SOURCE_QUALIFIED_NATIVE_READ")
        m["sourceTask"] = {"repo": "dvikt33-ux/safe-bim-layer",
                           "ref": "main",
                           "path": "examples/accelerator/bdd-house.json",
                           "blobSha1": "a"*40}
        with self.assertRaisesRegex(ValueError, "READ_TASK_NOT_PINNED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_replay_when_attempt_exists(self):
        with unittest.mock.patch.object(bridge, "STATE") as state:
            # Only durable-report publication is allowed after an attempt.
            with unittest.mock.patch.object(bridge, "remote_json", side_effect=AssertionError("REEXECUTED")):
                with unittest.mock.patch.object(bridge, "upload_result", return_value=None):
                    with unittest.mock.patch("pathlib.Path.is_dir", return_value=True):
                        with unittest.mock.patch("pathlib.Path.exists", return_value=False):
                            bridge.process_job("bdd114-roof-20261017")


class RuntimeReceiptTests(TestCase):
    def test_expanded_dependency_receipt_is_local_and_allowlisted(self):
        helpers={'apa_ac29_reusable_native_copy.py','apa_ac29_multi_prototype_native_copy.py',
                 'apa_ac29_scene_reconciliation.py'}
        modules=set(bridge.MODULE_HASHES)|helpers|{
            'apa_ac29_dynamic_write_scopes.py','apa_ac29_dynamic_native_verifiers.py'}
        with TemporaryDirectory() as td:
            root=Path(td);(root/'controllers').mkdir()
            receipt={'schema':'APA_AC29_RUNTIME_RELEASE_V1','revision':'a'*40,
                'workerSHA256':bridge.sha(Path(bridge.__file__)),
                'moduleHashes':{name:'b'*64 for name in modules},
                'controllerHashes':{name:'b'*64 for name in helpers},
                'workingPlnSha256':'c'*64,'expectedGuidCount':298}
            path=root/'controllers/runtime-release.json'
            path.write_text(json.dumps(receipt),encoding='utf8')
            with patch.object(bridge,'ROOT',root):
                self.assertEqual(bridge.approved_guid_count(),298)
                self.assertEqual(bridge.approved_saved_sha(),'c'*64)
                receipt['controllerHashes']['../foreign.py']='b'*64
                path.write_text(json.dumps(receipt),encoding='utf8')
                with self.assertRaisesRegex(ValueError,'CONTROLLER_RECEIPT_INVALID'):
                    bridge.runtime_release()


if __name__ == "__main__":
    unittest.main()
