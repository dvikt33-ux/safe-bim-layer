"""Selected library identity, physical-height distinction and no-replay proof."""
import copy,sqlite3,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_selected_library_part as L
GUID='75DBC58A-E1D7-4096-9294-BB578516AD4C'
NAME='TN_Аэратор_Кровельный_ТехноНИКОЛЬ_ЭКО_75х340'
class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.part={'documentName':NAME,'guid':GUID,'toolLookupError':0,'toolType':'Object'}
    def api(self,command,params):return {'libraryParts':[self.part],'skippedCount':92}
    def test_unicode_exact_identity_and_partial_catalog(self):
        result=L.resolve(self.api,NAME,GUID)
        self.assertEqual(result['part']['documentName'],NAME)
        self.assertFalse(result['completeCatalog']);self.assertEqual(result['skippedCount'],92)
    def test_ambiguous_name_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS'):
            L.resolve(lambda c,p:{'libraryParts':[self.part,self.part],'skippedCount':0},NAME,GUID)
    def test_foreign_guid_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'GUID'):
            L.resolve(self.api,NAME,'61682A57-134B-4EF0-A3A4-AC1006308694')
    def test_failed_tool_lookup_is_rejected(self):
        self.part['toolLookupError']=1
        with self.assertRaisesRegex(ValueError,'TOOL_UNVERIFIED'):L.resolve(self.api,NAME,GUID)
    def test_library_identity_is_bound_to_plan_hash(self):
        plan={'schemaSha256':'schema'};before=L.A.RUN.native_plan_hash(plan,'graph')
        plan['nativeLibraryExpectations']={'object':{'name':NAME,'guid':GUID}}
        self.assertNotEqual(before,L.A.RUN.native_plan_hash(plan,'graph'))
    def test_wrong_object_dimension_is_rejected(self):
        expected={'libraryPartName':NAME,'coordinates':{'x':55,'y':45,'z':0},'dimensions':{'x':.27,'y':.27,'z':.34}}
        details={'libPart':{'name':NAME},'origin':expected['coordinates'],'dimensions':{'x':.27,'y':.27,'z':.31}}
        with self.assertRaisesRegex(ValueError,'DIMENSIONS_READBACK'):
            L.A.RUN.verify_readback('CreateObjects',{'objectsData':[expected]}, {'type':'Object','floorIndex':0,'details':details})
    def test_physical_height_is_not_replaced_with_gdl_parameter_height(self):
        native={'elements':[{'guid':GUID,'type':'Object','homeStory':0,'bodies':[
            {'vertices':[[54.865,44.865,0],[55.135,45.135,.31]]}]}]}
        with patch.object(L.G,'normalize_dump',return_value=native):
            r=L.verify_geometry({},GUID,{'x':55,'y':45,'z':0},{'x':.27,'y':.27,'z':.34})
            self.assertAlmostEqual(r['physicalHeight'],.31)
            self.assertFalse(r['parameterHeightEqualsPhysicalHeight'])
            native['elements'][0]['bodies'][0]['vertices'][1][0]=55.2
            with self.assertRaisesRegex(ValueError,'XY_SIZE_OR_CENTER'):L.verify_geometry({},GUID,{'x':55,'y':45,'z':0},{'x':.27,'y':.27,'z':.34})
    def test_import_timeout_cannot_be_replayed(self):
        calls=[]
        binding={'path':L.A.RUN.APPROVED_ISOLATED_WRITER_PATH}
        source={'preflight':{'storyBindings':[{}],'binding':binding},'created':{},'inventory':[]}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);gsm=path/'synthetic.gsm';gsm.write_bytes(b'synthetic')
            files=[{'inputPath':str(gsm),'outputPath':'APA_Selected_TN_20261011/synthetic.gsm','type':'Object'}]
            def api(command,params):
                if command=='GetAvailableLibraryParts':return {'libraryParts':[],'skippedCount':0}
                calls.append(command);raise TimeoutError('UNKNOWN_OUTCOME')
            with patch.object(L.A.RUN,'guarded_project',return_value=binding),patch.object(L.A,'inventory_guids',return_value=[]),patch.object(L.E,'verify_model',return_value={}):
                r=L.import_selected(api,source,files,NAME,GUID,path/'journal.sqlite3','selected-import-01')
                with self.assertRaises(sqlite3.IntegrityError):L.import_selected(api,source,files,NAME,GUID,path/'journal.sqlite3','selected-import-01')
            self.assertEqual(calls,['AddFilesToEmbeddedLibrary'])
            self.assertEqual(r['status'],'PARTIAL_OR_UNKNOWN_OUTCOME');self.assertFalse(r['automaticRetry'])
