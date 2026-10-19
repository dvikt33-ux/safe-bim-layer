"""Thin ready-vendor adapter tests; no Archicad or dependency installation."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import apa_dxf_source_preflight as D
try:import ezdxf
except ImportError:ezdxf=None

@unittest.skipUnless(ezdxf,'ezdxf1.4.5 vendor runtime required')
class DrawingTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
    def drawing(self,xref=True):
        doc=ezdxf.new('R2010');doc.units=4
        block=doc.blocks.new('prototype');block.add_line((0,0),(1,0))
        insert=doc.modelspace().add_blockref('prototype',(0,0));insert.dxf.row_count=2;insert.dxf.column_count=3
        insert.dxf.row_spacing=10;insert.dxf.column_spacing=20
        if xref:doc.add_xref_def('target.dxf','external')
        return doc
    def test_matrix_units_xref_hash_and_source_bytes_preserved(self):
        target=self.root/'target.dxf';target.write_bytes(b'fixed referenced source bytes')
        source=self.root/'source.dxf';self.drawing().saveas(source);before=D.digest(source)
        r=D.analyze_file(source);v=r['result']
        self.assertEqual(v['insunitsCode'],4);self.assertEqual(v['inserts']['nominalMatrixSlots'],6)
        self.assertEqual(v['inserts']['ezdxfEffectiveInsertCount'],6)
        self.assertEqual(v['xrefs'][0]['sha256'],hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(D.digest(source),before);self.assertEqual(r['nativeCalls'],0)
        self.assertFalse(v['automaticBIMWriteAllowed'])
    def test_missing_xref_and_unitless_are_not_ready(self):
        doc=self.drawing();doc.units=0;source=self.root/'source.dxf';doc.saveas(source)
        v=D.analyze_file(source)['result'];self.assertFalse(v['readyForFurtherSourceAnalysis'])
        self.assertEqual(v['xrefs'][0]['status'],'MISSING_LOCAL_FILE');self.assertFalse(v['unitsDeclared'])
    def test_outside_or_remote_xref_is_never_opened(self):
        doc=self.drawing();block=doc.blocks['external'].block
        for raw in ('../outside.dxf',r'\\server\private\file.dxf','https://example.invalid/file.dxf'):
            block.dxf.xref_path=raw
            record=D.xref_record(block,self.root,[D.MAX_BYTES])
            self.assertTrue(record['status'].endswith('NOT_READ'));self.assertNotIn('sha256',record)
    def test_zero_spacing_has_effective_count_from_vendor_without_expansion(self):
        doc=self.drawing(False);insert=list(doc.modelspace().query('INSERT'))[0];insert.dxf.row_spacing=0
        v=D.analyze(doc,doc.audit(),self.root)
        self.assertEqual(v['inserts']['nominalMatrixSlots'],6);self.assertEqual(v['inserts']['ezdxfEffectiveInsertCount'],3)
        self.assertFalse(v['inserts']['virtualGeometryCreated'])
    def test_recovered_document_or_in_memory_fixes_never_become_ready(self):
        doc=self.drawing(False);v=D.analyze(doc,doc.audit(),self.root,'RECOVERED_IN_MEMORY_REVIEW_REQUIRED')
        self.assertFalse(v['readyForFurtherSourceAnalysis']);self.assertFalse(v['repairedDrawingSaved'])

class RegistryTests(unittest.TestCase):
    def test_existing_router_registers_code_owned_read_only_handler(self):
        from archicad_dynamic_commands import DynamicCommands
        import archicad_project_accelerator as A
        root=Path(__file__).resolve().parents[1]
        router=DynamicCommands(A.catalog_with_provenance(root/'schemas/tapir-live-1.5.10/tapir-scene-live.json'));before={k:router.contract_hash(k) for k in router.catalog['commands']}
        D.register(router)
        self.assertEqual(router.operation_kind(D.CMD),'READ_ONLY')
        self.assertEqual(before,{k:router.contract_hash(k) for k in before})
        ticket=router.prepare(D.CMD,dict(a='explicit.dxf',output='fresh.json'))
        self.assertEqual(ticket['effect'],'READ_ONLY')

if __name__=='__main__':unittest.main()
