"""Exact installed delta and rollback; synthetic filesystem only."""
from pathlib import Path
import tempfile,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import apa_update_copy_registry as U
SOURCE=Path(__file__).resolve().parents[1]

class Update(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.old={'scripts/archicad_project_accelerator.py':b'READS=frozenset()\nUSER_CODE=29\n',
            'scripts/archicad_dynamic_commands.py':b'# original prefix\nclass DynamicCommands:\n    def scope(self,*args):\n        return "old"\n    def user_method(self):\n        return 29\n# original suffix\n',
            'scripts/apa_ac29_dynamic_native_verifiers.py':b'# prefix\ndef installed_verifiers():\n    return {}\n# suffix\n'}
        for n,b in self.old.items():p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        p=patch.object(U,'PINNED',{n:U.sha(b) for n,b in self.old.items()});p.start();self.addCleanup(p.stop)

    def test_only_scope_method_changes_and_old_user_code_survives(self):
        _,before,new=U.preflight(self.root,SOURCE)
        self.assertEqual(before,self.old)
        d=new['scripts/archicad_dynamic_commands.py']
        self.assertTrue(d.startswith(b'# original prefix\nclass DynamicCommands:\n'))
        self.assertTrue(d.endswith(b'    def user_method(self):\n        return 29\n# original suffix\n'))
        self.assertTrue(new['scripts/archicad_project_accelerator.py'].startswith(self.old['scripts/archicad_project_accelerator.py']))

    def test_existing_delta_module_is_never_overwritten(self):
        p=self.root/U.ADD[0];p.write_bytes(b'custom')
        with self.assertRaisesRegex(ValueError,'ADDITION_ALREADY_EXISTS'):U.preflight(self.root,SOURCE)
        self.assertEqual(p.read_bytes(),b'custom')

    def test_installed_dynamic_drift_blocks_all_writes(self):
        (self.root/'scripts/archicad_dynamic_commands.py').write_bytes(b'edited')
        with self.assertRaisesRegex(ValueError,'HASH_DRIFT'):U.preflight(self.root,SOURCE)

    def test_failed_smoke_restores_all_three_originals_and_removes_own_new_files(self):
        def fail(root):raise ValueError('FAILED_SMOKE')
        with self.assertRaisesRegex(ValueError,'FAILED_SMOKE'):U.install(self.root,SOURCE,fail)
        for n,b in self.old.items():self.assertEqual((self.root/n).read_bytes(),b)
        self.assertTrue(all(not (self.root/n).exists() for n in U.ADD))

    def test_success_preserves_original_backups(self):
        r=U.install(self.root,SOURCE,lambda root:None)
        self.assertEqual(r['status'],'INSTALLED_COPY_REGISTRY_READBACK_VERIFIED')
        for n,b in self.old.items():self.assertEqual((Path(r['backup'])/n).read_bytes(),b)

if __name__=='__main__':unittest.main()
