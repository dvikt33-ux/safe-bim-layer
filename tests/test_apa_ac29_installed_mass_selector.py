"""Offline staged installation/rollback and existing Router contracts."""
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import apa_install_mass_selector as I
import apa_ac29_installed_group_provider as P

SOURCE=Path(__file__).resolve().parents[1]


class InstallGates(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name)/'installed';self.root.mkdir()
        self.original={
          'scripts/archicad_project_accelerator.py':b'# prefix\nvalue=7\ndef prepare_auto_optimized_native_task(router,intent,planner_python=None):\n    return "legacy"\n# suffix\ndef retained_user_function():\n    return 29\n',
          'scripts/apa_ac29_dynamic_native_verifiers.py':b'# prefix\ndef installed_verifiers():\n    return {}\n# suffix\n'}
        for n,b in self.original.items():
            p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        self.p=patch.object(I,'PINNED',{n:I.sha(b) for n,b in self.original.items()});self.p.start();self.addCleanup(self.p.stop)

    def test_preflight_never_changes_current_core(self):
        root,old,new=I.preflight(self.root,SOURCE)
        self.assertEqual(old,self.original)
        for n,b in old.items():self.assertEqual((root/n).read_bytes(),b)
        core=new['scripts/archicad_project_accelerator.py']
        self.assertTrue(core.startswith(b'# prefix\nvalue=7\n'))
        self.assertIn(b'# suffix\ndef retained_user_function():\n    return 29\n',core)
        self.assertIn(b'def prepare_current_runtime_group_native_task',core)

    def test_hash_drift_denies_update(self):
        (self.root/'scripts/archicad_project_accelerator.py').write_bytes(b'user edited')
        with self.assertRaisesRegex(ValueError,'HASH_DRIFT'):I.preflight(self.root,SOURCE)

    def test_existing_different_module_is_preserved(self):
        p=self.root/'scripts/apa_ac29_mass_request.py';p.write_bytes(b'custom')
        with self.assertRaisesRegex(ValueError,'NO_OVERWRITE'):I.preflight(self.root,SOURCE)
        self.assertEqual(p.read_bytes(),b'custom')

    def test_apply_requires_explicit_smoke(self):
        with self.assertRaisesRegex(ValueError,'SMOKE_REQUIRED'):I.install(self.root,SOURCE,apply=True)

    def test_failed_smoke_restores_original_and_only_removes_own_additions(self):
        def fail(root):raise ValueError('smoke fails')
        with self.assertRaisesRegex(ValueError,'smoke fails'):I.install(self.root,SOURCE,apply=True,smoke=fail)
        for n,b in self.original.items():self.assertEqual((self.root/n).read_bytes(),b)
        self.assertFalse((self.root/'scripts/apa_ac29_mass_request.py').exists())
        self.assertEqual(len(list((self.root/'runtime-code-backups').glob('*/receipt.json'))),1)

    def test_success_has_exact_backups_and_new_byte_readback(self):
        r=I.install(self.root,SOURCE,apply=True,smoke=lambda root:None)
        self.assertTrue(r['applied']);self.assertEqual(r['modelWrites'],0)
        for n,b in self.original.items():self.assertEqual((Path(r['backup'])/n).read_bytes(),b)
        for n,row in r['files'].items():self.assertEqual(I.sha((self.root/n).read_bytes()),row['afterSHA256'])


class ExistingRouterProvider(unittest.TestCase):
    def router(self):
        from archicad_dynamic_commands import DynamicCommands
        from archicad_batch_contracts import load_catalog
        return DynamicCommands(load_catalog(SOURCE/'tapir-1.5.8.json'))

    def test_two_contract_attachment_idempotent_and_unprobed(self):
        r=self.router();before=set(r.catalog['commands']);P.attach(r);count=len(r.catalog['commands'])
        P.attach(r);self.assertEqual(len(r.catalog['commands']),count)
        self.assertEqual(len(set(r.catalog['commands'])-before),2)
        self.assertEqual(r.operation_kind('AddOn.TapirCommand.CloneNativeGroupV1'),'CREATE')
        self.assertIsNot(r.registration.get('AddOn.TapirCommand.CloneNativeGroupV1'),True)

    def test_existing_contract_drift_rejected(self):
        r=self.router();P.attach(r)
        r.catalog['commands']['AddOn.TapirCommand.CloneNativeGroupV1']['version']='wrong'
        with self.assertRaisesRegex(ValueError,'CONTRACT_DRIFT'):P.attach(r)

    def test_runtime_identity_must_equal_accepted_build(self):
        accepted=P.contract()['acceptedRuntime']
        self.assertEqual(P.verify_runtime(lambda *a:accepted),accepted)
        with self.assertRaisesRegex(ValueError,'UNACCEPTED_NATIVE_RUNTIME'):
            P.verify_runtime(lambda *a:dict(accepted,buildIdentity='0'*64))


if __name__=='__main__':unittest.main()
