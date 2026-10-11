"""Synthetic negatives and one-shot journal behavior; no native calls."""
import copy,sqlite3,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_native_material_selection as M
import archicad_authored_extension as E

GUID='61682A57-134B-4EF0-A3A4-AC1006308694'
class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.header={'attributeId':{'guid':GUID},'name':'HEA200'}
        self.headers=[self.header]
    def api(self,command,params):
        return {'attributes':self.headers} if command=='GetAttributesByType' else {'profiles':[self.header]}
    def test_exact_project_name_guid_and_detail_identity_are_required(self):
        self.assertEqual(M.resolve(self.api,'Profile','HEA200',GUID),self.header)
    def test_ambiguous_name_is_not_resolved_by_first_match(self):
        self.headers.append(copy.deepcopy(self.header))
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS'):M.resolve(self.api,'Profile','HEA200',GUID)
    def test_foreign_project_guid_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'GUID_MISMATCH'):M.resolve(self.api,'Profile','HEA200','436C450E-7CE3-6C48-A75D-68BC4A792483')
    def test_attribute_detail_identity_mismatch_is_rejected(self):
        def api(command,params):
            return {'attributes':self.headers} if command=='GetAttributesByType' else {'profiles':[{'attributeId':{'guid':GUID},'name':'other'}]}
        with self.assertRaisesRegex(ValueError,'DETAIL_IDENTITY'):M.resolve(api,'Profile','HEA200',GUID)
    def test_profile_area_preserves_holes_with_native_one_based_contours(self):
        coords=[{'x':0,'y':0}]+[{'x':x,'y':y} for x,y in [(0,0),(2,0),(2,2),(0,2),(0,0),(.5,.5),(1.5,.5),(1.5,1.5),(.5,1.5),(.5,.5)]]
        p={'skins':[{'outlineCoords':coords,'outlineSubPolyEnds':[0,5,10],'outlineArcs':[]}]}
        self.assertAlmostEqual(M.profile_area(p),3.)
    def test_curved_profile_is_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError,'CURVED_PROFILE'):
            M.profile_area({'skins':[{'outlineArcs':[{}]}]})
    def test_missing_profile_outline_is_not_an_aabb_pass(self):
        with self.assertRaisesRegex(ValueError,'OUTLINE_INDEX_COVERAGE'):
            M.profile_area({'skins':[{'outlineArcs':[]}]})
    def test_profile_guid_mismatch_is_rejected_by_existing_typed_readback(self):
        params={'columnsData':[{'coordinates':{'x':0,'y':0,'z':0},'width':.2,'depth':.19,'height':3,'profileId':{'guid':GUID}}]}
        row={'type':'Column','floorIndex':0,'details':{'origin':{'x':0,'y':0},'zCoordinate':0,'width':.2,'depth':.19,'height':3,'profileId':{'guid':'wrong'}}}
        with self.assertRaisesRegex(ValueError,'PROFILE_READBACK'):E.RUN.verify_readback('CreateColumns',params,row)
    def test_surface_expectations_change_bound_hash_without_changing_graph(self):
        plan={'schemaSha256':'source-schema','slabLevelConvention':'PROJECT_ABSOLUTE'}
        before=E.RUN.native_plan_hash(plan,'same-graph')
        plan['nativeAttributeExpectations']={'wall-a':{'referenceMaterial':{'overridden':True,'attributeId':{'guid':GUID}}}}
        self.assertNotEqual(before,E.RUN.native_plan_hash(plan,'same-graph'))
    def test_wrong_surface_override_is_rejected_by_existing_typed_readback(self):
        data={'begCoordinate':{'x':0,'y':0},'endCoordinate':{'x':2,'y':0},'height':3,'thickness':.3,'offset':0,'arcAngle':0,'zCoordinate':0,
            'referenceMaterial':{'overridden':True,'attributeId':{'guid':GUID}}}
        row={'type':'Wall','floorIndex':0,'details':{'begCoordinate':data['begCoordinate'],'endCoordinate':data['endCoordinate'],
            'height':3,'begThickness':.3,'endThickness':.3,'offset':0,'arcAngle':0,'zCoordinate':0,'structureType':'Basic',
            'referenceLineLocation':'Center','geometryType':'Straight','referenceMaterial':{'overridden':False}}}
        with self.assertRaisesRegex(ValueError,'SURFACE_OVERRIDE'):E.RUN.verify_readback('CreateWalls',{'wallsData':[data]},row)

class AttributeJournalTests(unittest.TestCase):
    def exercise(self,timeout):
        calls=[]
        with tempfile.TemporaryDirectory() as tmp:
            journal=Path(tmp)/'journal.sqlite3'
            plan={'binding':{'path':E.RUN.APPROVED_ISOLATED_WRITER_PATH},'storyBindings':[{}],'sourcePlanHash':'hash'}
            record={'operationId':'material-once-01','oldPlan':plan,'newPlan':plan,'inventory':[],'created':{},'columnSegments':{},'command':'ModifyWalls','parameters':{}}
            ticket=E._reserve_attribute_ticket(record,journal)
            def api(command,params):
                calls.append(command)
                if timeout:raise TimeoutError('UNKNOWN_OUTCOME')
                return {'executionResults':[{'success':True}]}
            with patch.object(E.RUN,'guarded_project',return_value=plan['binding']),patch.object(E.A,'inventory_guids',return_value=[]),patch.object(E.A,'column_subelements',return_value={}),patch.object(E,'verify_model',return_value={}):
                result=E.execute_attribute_edit(api,ticket,journal,ticket['confirmPlanHash'])
                with self.assertRaises(sqlite3.IntegrityError):E.execute_attribute_edit(api,ticket,journal,ticket['confirmPlanHash'])
            self.assertEqual(calls,['ModifyWalls']);self.assertFalse(result['automaticRetry'])
            return result
    def test_successful_edit_cannot_be_replayed(self):
        self.assertEqual(self.exercise(False)['status'],'EXISTING_ATTRIBUTE_EDIT_READBACK_PASS')
    def test_timeout_remains_unknown_and_cannot_be_replayed(self):
        self.assertEqual(self.exercise(True)['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
