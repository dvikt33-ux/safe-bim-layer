import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands
ROOT=Path(__file__).resolve().parents[1]
def connected():
    r=DynamicCommands(json.loads((ROOT/'schemas/accelerator/mass-capabilities/commands.json').read_text(encoding='utf8')))
    A.connect_functional_modules(r);return r
class FunctionalModules(unittest.TestCase):
    def test_quarantined_quantity_stays_preparable_and_cannot_reach_transport(self):
        r=connected();ticket=r.prepare('AddOn.TapirCommand.GetNativeElementQuantitiesV1',
            dict(elements=[{'elementId':{'guid':'diagnostic-only'}}],minOpeningSize=0))
        with self.assertRaisesRegex(ValueError,'COMMAND_RUNTIME_QUARANTINED'):
            r.read(None,ticket,True)
        # A live export uses the unqualified Tapir command name. Code-owned
        # quarantine must also apply when the command was already discovered.
        catalog=json.loads((ROOT/'schemas/accelerator/mass-capabilities/commands.json').read_text())
        row=json.loads((ROOT/'schemas/accelerator/functional-modules.json').read_text())['sdkProviders']['TapirCommand']['GetNativeElementQuantitiesV1']
        catalog['commands']['GetNativeElementQuantitiesV1']={k:v for k,v in row.items() if k!='executionBlocker'}
        r=DynamicCommands(catalog);A.connect_functional_modules(r)
        with self.assertRaisesRegex(ValueError,'COMMAND_RUNTIME_QUARANTINED'):
            r.read(None,r.prepare('GetNativeElementQuantitiesV1',ticket['parameters']),True)
    def test_memo_flow_preserves_holes_and_excludes_curves_and_other_tools(self):
        from apa_native_memo_flow import run
        points=[[0,0],[6,0],[6,6],[0,6],[0,0],[2,2],[4,2],[4,4],[2,4],[2,2]]
        row=dict(elementId={'guid':'test-slab'},nativeTypeId=8,homeStory=0,
            coordinates=[dict(index=i+1,x=p[0],y=p[1]) for i,p in enumerate(points)],contourEnds=[5,10],arcs=[])
        curved=dict(row,elementId={'guid':'curve'},arcs=[dict(beginIndex=1,endIndex=2,angle=1)])
        other=dict(row,elementId={'guid':'shell'},nativeTypeId=44)
        proof=run(dict(elements=[row,curved,other]))
        self.assertEqual(proof['convertedElements'],1);self.assertEqual(proof['preservedHoles'],1)
        self.assertEqual(proof['polygonMeasures'][0]['area'],32)
        self.assertIn('CURVED_EDGES_NOT_LINEARIZED',proof['omittedReasons'])
        self.assertEqual(proof['nativeModelWrites'],0)
    def test_attachment_drift_idempotence_and_no_native_permission(self):
        r=connected();before=r.fingerprint;A.connect_functional_modules(r);self.assertEqual(r.fingerprint,before)
        self.assertEqual(len(r.catalog['commands']),385)
        manifest=json.loads((ROOT/'schemas/accelerator/functional-modules.json').read_text(encoding='utf8'));manifest['local']['implementationSHA256']='0'*64
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'manifest.json';path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'LOCAL_MODULE_SOURCE_DRIFT'):A.connect_functional_modules(r,path)
        self.assertFalse(r.prepare('AddOn.TapirCommand.GetNativeWorkingUnitsV1',{})['nativeWritePermission'])
    def test_local_graph_cycle_and_hole_preservation_without_transport(self):
        r=connected();call=lambda n,p:r.read(None,r.prepare('AddOn.APAAnalysis.'+n,p),True)
        impact=call('DependencyImpact',dict(nodes=['floor','wall','window'],edges=[['floor','wall'],['wall','window']],changed=['floor']))
        self.assertEqual(impact['updateOrder'],['floor','wall','window'])
        cycle=call('DependencyImpact',dict(nodes=['a','b'],edges=[['a','b'],['b','a']],changed=['a']))
        self.assertFalse(cycle['executionAllowed']);self.assertEqual(cycle['status'],'CYCLIC')
        facts=call('PolygonRelations',dict(polygons=[dict(id='slab',outline=[[0,0],[6,0],[6,6],[0,6]],holes=[[[2,2],[4,2],[4,4],[2,4]]]),dict(id='inside-hole',outline=[[2.1,2.1],[3.9,2.1],[3.9,3.9],[2.1,3.9]])]))
        self.assertEqual(facts['polygons'][0]['area'],32);self.assertEqual(facts['relations'],[])
        self.assertTrue(all(e['nativeWrites']==0 for e in r.local_events))
    def test_local_schema_validation_dependency_flow_and_cpsat(self):
        r=connected()
        with self.assertRaises(Exception):r.prepare('AddOn.APAAnalysis.PolygonRelations',dict(polygons=[],tolerance=-1))
        answer=r.read(None,r.prepare('AddOn.APAAnalysis.ConstrainedAssignment',dict(tasks=[dict(id='one',costs={'a':1,'b':8}),dict(id='two',costs={'a':2,'b':3})],capacities={'a':1,'b':1})),True)
        self.assertEqual(answer['status'],'OPTIMAL');self.assertEqual(answer['objective'],4)
        graph=dict(operations=[dict(id='select',command='AddOn.APAAnalysis.IFCSelect',params=dict(path='explicit-input.ifc',query='IfcWall')),dict(id='geometry',command='AddOn.APAAnalysis.IFCGeometry',params={'path':'explicit-input.ifc','guids':[{'$result':dict(step='select',pointer='/elements/0/ifcId')}]})])
        plan=r.prepare_workflow(graph);self.assertEqual(plan['executionOrder'],['select','geometry']);self.assertFalse(plan['executionPermission'])
class ComponentContextIntegration(unittest.TestCase):
    def test_new_group_contracts_are_preparable_without_granting_runtime(self):
        r=connected()
        for name in ['GetNativeComponentBindingsV1','GetNativeOpeningConnectionsV1','GetNativeQuantityPreflightV1']:
            ticket=r.prepare('AddOn.TapirCommand.'+name,dict(elements=[dict(elementId=dict(guid='contract-only'))]))
            self.assertFalse(ticket.get('executionPermission',False))
        r.prepare('AddOn.TapirCommand.GetNativeDrawingAssociationsV1',dict(elements=[dict(elementId=dict(guid='drawing'),databaseId=dict(guid='layout'))]))
        schema=r.catalog['commands']['AddOn.TapirCommand.GetNativeEnvelopeMemoV1']['returns']
        self.assertIn('pivotEdgeOverrides',json.dumps(schema));self.assertIn('sideMaterials',json.dumps(schema))

    def test_native_relationships_feed_existing_dependency_graph_without_self_loops(self):
        from apa_native_dependency_flow import run
        components=dict(elements=[dict(elementId=dict(guid='tread'),parentElementId=dict(guid='stair'),rootElementId=dict(guid='stair'),parentQueryError=0,rootQueryError=0)])
        answer=run(connected(),dict(components=components),['stair'])
        self.assertEqual(answer['result']['updateOrder'],['STAIR','TREAD'])
        self.assertFalse(answer['executionPermission']);self.assertEqual(len(answer['inputs']['edges']),1)

    def test_failed_relationships_and_unknown_view_are_not_inferred(self):
        from apa_native_dependency_flow import dependency_inputs
        facts=dependency_inputs(components=dict(elements=[dict(elementId=dict(guid='self'),parentElementId=dict(guid='self'),parentQueryError=0),dict(error=dict(code=-1))]),
            drawings=dict(drawings=[dict(elementId=dict(guid='drawing'),linkGuid=dict(guid='unknown'),viewDeleted=False)]))
        self.assertEqual(facts['edges'],[])
        self.assertEqual(len(facts['omitted']),2)

if __name__=='__main__':unittest.main()
