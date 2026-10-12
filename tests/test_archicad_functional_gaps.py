import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import archicad_details_context as D
import archicad_native_mep_network as M
import archicad_native_operations as O
import archicad_connected_ifc as IFC
C=O.C
def guid(n):return '00000000-0000-4000-8000-'+str(n).zfill(12)


def native_fixture():
    system=guid(1);routes=[];ports=[]
    for i,(a,b) in enumerate([(0,1),(1,2)]):
        physical=guid(20+i);position=lambda x:{'x':x,'y':0.,'z':1.}
        routes.append({'domain':'Ventilation','mepSystemId':{'guid':system},'polyline':[position(a),position(b)],
            'nodes':[{'elementId':{'guid':guid(30+2*i+j)},'position':position(x)} for j,x in enumerate([a,b])],
            'segments':[{'elementId':{'guid':guid(40+i)},'crossSectionWidth':.2,'crossSectionHeight':.15,'crossSectionShape':'Rectangular'}]})
        row=[]
        for j,x in enumerate([a,b]):
            p={'portId':guid(50+2*i+j),'position':position(x),'direction':{'x':(-1 if j==0 else 1),'y':0,'z':0},
                'domain':'Ventilation','mepSystemId':{'guid':system},'width':.2,'height':.15,'shape':'Rectangular','isPhysicallyConnected':x==1}
            if x==1:p.update(connectedPortId=guid(52 if i==0 else 51),connectedElementId={'guid':guid(21 if i==0 else 20)})
            row.append(p)
        ports.append({'ports':row})
    replies={'GetMEPRoutingElements':{'routingElements':routes},'GetMEPDistributionSystems':{'distributionSystems':[
        {'domain':'Ventilation','mepSystemId':{'guid':system},'elements':[{'elementId':{'guid':guid(20+i)}} for i in range(2)]}]},
        'GetMEPPorts':{'elementPorts':ports},'GetMEPElements':{'elements':[]}}
    return replies,lambda command,params:copy.deepcopy(replies[command])


class DetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.adapter=D.DetailsContext(ROOT)
    def context(self):
        return {'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':{'wall':{'guid':guid(2),'kind':'Wall',
            'floorIndex':0,'bounds':[[[0.,2.],[0.,.3],[0.,3.]]],'materialBindings':{'buildingMaterialGuid':guid(3)}}}}
    def test_all_73_source_verified_and_joined(self):
        r=self.adapter.evaluate(self.context());self.assertEqual(r['contextDetailCount'],73)
        self.assertEqual(len({d['detailId'] for d in r['details']}),73)
        self.assertTrue(all(d['resolvedFacts'] for d in r['details']))
    def test_source_product_is_not_inferred_from_wall_type(self):
        r=self.adapter.evaluate(self.context());self.assertTrue(all(d['bindings'][0]['applicability']=='NOT_APPLICABLE_OR_UNRESOLVED' for d in r['details']))
    def test_all_source_gates_preserved_independently(self):
        r=self.adapter.evaluate(self.context());self.assertTrue(all(not d['assemblyWriteAllowed'] and d['compileBlockers'] for d in r['details']))
    def test_exchange_is_host_bound_and_detached(self):
        r=self.adapter.evaluate(self.context());d=r['details'][0];e=self.adapter.exchange(r,d['detailId'],guid(2));e['bindings'][0]['floorIndex']=9
        self.assertEqual(d['bindings'][0]['floorIndex'],0)
    def test_unknown_detail_rejected(self):
        with self.assertRaises(ValueError):self.adapter.exchange(self.adapter.evaluate(self.context()),'invented',guid(2))
    def test_unverified_host_rejected(self):
        r=self.adapter.evaluate(self.context())
        with self.assertRaises(ValueError):self.adapter.exchange(r,r['details'][0]['detailId'],guid(99))
    def test_world_unit_gate(self):
        c=self.context();c['units']='mm'
        with self.assertRaises(ValueError):self.adapter.evaluate(c)
    def test_actual_manufacturer_missing_eight_does_not_block_context(self):
        r=C.details_candidate(ROOT,'ARMO_SELFLOCK_ROOF__P0003',{'guid':guid(2),'kind':'Roof','floorIndex':1})
        self.assertEqual(len(r['missingDimensionEntities']),8);self.assertEqual(len(self.adapter.evaluate(self.context())['details']),73)
    def test_qualified_product_still_cannot_override_source_dimensions(self):
        c=self.context();record=next(iter(self.adapter.records.values()));product=record['source_products_in_title'][0]
        r=self.adapter.evaluate(c,{guid(2):{'sourceProduct':product,'nativeMaterialBindings':c['elements']['wall']['materialBindings']}})
        self.assertFalse(any(d['assemblyWriteAllowed'] for d in r['details']))


class NetworkTests(unittest.TestCase):
    def read(self,replies=None):
        r,api=native_fixture()
        if replies is not None:api=lambda cmd,params:copy.deepcopy(replies[cmd])
        return M.read_network(api,[guid(10),guid(11)],guid(1))
    def test_reciprocal_native_network_even_when_generic_query_empty(self):
        r=self.read();self.assertTrue(r['physicalConnected']);self.assertTrue(r['logicalConnected'])
        self.assertEqual((r['segmentCount'],r['nodeCount'],r['physicalConnectionEdges'],r['genericEnumerationCount']),(2,4,1,0))
    def test_already_connected_no_extra_write(self):self.assertEqual(M.connection_intent(self.read(),guid(10),guid(11))['nativeWritesRequired'],0)
    def test_open_outer_endpoints_are_explicit(self):self.assertEqual(len(self.read()['openPorts']),2)
    def test_wrong_system_rejected(self):
        r,_=native_fixture();r['GetMEPRoutingElements']['routingElements'][0]['mepSystemId']={'guid':guid(99)}
        with self.assertRaises(ValueError):self.read(r)
    def test_bad_nominal_section_rejected(self):
        r,_=native_fixture();r['GetMEPRoutingElements']['routingElements'][0]['segments'][0]['crossSectionHeight']=0
        with self.assertRaises(ValueError):self.read(r)
    def test_nonfinite_and_boolean_sections_rejected(self):
        for invalid in (float('nan'),float('inf'),True):
            r,_=native_fixture();r['GetMEPPorts']['elementPorts'][0]['ports'][0]['width']=invalid
            with self.assertRaises(ValueError):self.read(r)
    def test_one_way_connected_flag_rejected(self):
        r,_=native_fixture();r['GetMEPPorts']['elementPorts'][1]['ports'][0]['isPhysicallyConnected']=False
        with self.assertRaises(ValueError):self.read(r)
    def test_coincident_ports_do_not_imply_connection(self):
        r,_=native_fixture()
        for row in r['GetMEPPorts']['elementPorts']:
            for p in row['ports']:p['isPhysicallyConnected']=False
        n=self.read(r);self.assertFalse(n['physicalConnected']);self.assertFalse(n['logicalConnected'])
    def test_connected_section_mismatch_rejected(self):
        r,_=native_fixture();r['GetMEPPorts']['elementPorts'][1]['ports'][0]['width']=.3
        with self.assertRaises(ValueError):self.read(r)
    def test_connected_direction_mismatch_rejected(self):
        r,_=native_fixture();r['GetMEPPorts']['elementPorts'][1]['ports'][0]['direction']['x']=1
        with self.assertRaises(ValueError):self.read(r)
    def test_missing_peer_rejected(self):
        r,_=native_fixture();r['GetMEPPorts']['elementPorts'][0]['ports'][1]['connectedPortId']=guid(99)
        with self.assertRaises(ValueError):self.read(r)
    def test_self_connection_rejected(self):
        with self.assertRaises(ValueError):M.connection_intent(self.read(),guid(10),guid(10))
    def test_unknown_route_rejected(self):
        with self.assertRaises(ValueError):M.connection_intent(self.read(),guid(10),guid(99))


class OperationTests(unittest.TestCase):
    def test_shell_absence_is_explicit(self):
        r=O.provider_scope(C.A.catalog_with_provenance(C.RUN.DEFAULT_SCENE_SCHEMA));self.assertEqual(r['CreateShells'],'UNSUPPORTED_INSTALLED_PROVIDER')
        self.assertIn('SCHEMA_AVAILABLE',r['CreateOpenings'])
    def test_seo_invalid_bounds_rejected_before_reads(self):
        with self.assertRaises(ValueError):O.seo_readback(None,guid(1),guid(2),{},[[0,0,0],[1,1,1]])
    def test_optional_wall_defaults_independently_read(self):
        p={'wallsData':[{'begCoordinate':{'x':0,'y':0},'endCoordinate':{'x':2,'y':0},'height':2,'thickness':.3,'zCoordinate':0}]}
        d={**p['wallsData'][0],'begThickness':.3,'endThickness':.3,'offset':0,'arcAngle':0,'structureType':'Basic','referenceLineLocation':'Center','geometryType':'Straight'}
        C.RUN.verify_readback('CreateWalls',p,{'type':'Wall','floorIndex':0,'details':d})
        d['offset']=.1
        with self.assertRaises(ValueError):C.RUN.verify_readback('CreateWalls',p,{'type':'Wall','floorIndex':0,'details':d})
    def test_bound_writer_hash_rejects_before_native(self):
        w=C.RUN.SceneWriter(None,'unused');p={'sourcePlanHash':'source','binding':{}}
        with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):w.execute_bound_operation(p,'valid-scene-001','CreateOpenings',{},'wrong',lambda:None,lambda a,b:None)
    def test_bound_writer_native_failure_reserved_no_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            calls=[]
            def api(command,parameters):calls.append(command);raise TimeoutError('unknown native outcome')
            w=C.RUN.SceneWriter(api,Path(folder)/'journal.sqlite');p={'sourcePlanHash':'source','binding':{'identity':'test'}}
            params={'openingsData':[{'ownerElementId':{'guid':guid(1)},'basePoint':{'x':0,'y':0,'z':0},'width':1,'height':1}]}
            intent={'sceneId':'bounded-opening-001','sourcePlanHash':'source','command':'CreateOpenings','parameters':params,'target':p['binding']};h=C.RUN.digest(intent)
            with patch.object(w,'guarded_binding',return_value=p['binding']):
                r=w.execute_bound_operation(p,intent['sceneId'],'CreateOpenings',params,h,lambda:{},lambda a,b:{})
                self.assertEqual(r['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
                with self.assertRaisesRegex(ValueError,'NEVER_RETRY'):w.execute_bound_operation(p,intent['sceneId'],'CreateOpenings',params,h,lambda:{},lambda a,b:{})
            self.assertEqual(calls,['CreateOpenings'])
    def test_bound_writer_rejects_multiple_targets_before_dispatch(self):
        w=C.RUN.SceneWriter(None,'unused');p={'sourcePlanHash':'source','binding':{}};params={'openingsData':[{},{}]}
        intent={'sceneId':'bounded-opening-002','sourcePlanHash':'source','command':'CreateOpenings','parameters':params,'target':p['binding']}
        with self.assertRaisesRegex(ValueError,'SINGLE_NATIVE_TARGET'):w.execute_bound_operation(p,intent['sceneId'],'CreateOpenings',params,C.RUN.digest(intent),lambda:{},lambda a,b:{})
    def test_bound_writer_requires_independent_pass_after_provider_success(self):
        with tempfile.TemporaryDirectory() as folder:
            w=C.RUN.SceneWriter(lambda c,p:{'elements':[{'elementId':{'guid':guid(2)}}]},Path(folder)/'journal.sqlite');p={'sourcePlanHash':'source','binding':{}}
            params={'openingsData':[{'ownerElementId':{'guid':guid(1)},'basePoint':{'x':0,'y':0,'z':0}}]}
            intent={'sceneId':'bounded-opening-003','sourcePlanHash':'source','command':'CreateOpenings','parameters':params,'target':p['binding']}
            with patch.object(w,'guarded_binding',return_value={}):
                r=w.execute_bound_operation(p,intent['sceneId'],'CreateOpenings',params,C.RUN.digest(intent),lambda:{},lambda a,b:None)
            self.assertEqual(r['status'],'PARTIAL_OR_UNKNOWN_OUTCOME');self.assertEqual(r['createdGuid'],guid(2))
    def test_ifc_physical_geometry_does_not_invent_analytical_members(self):
        import ifcopenshell
        with tempfile.TemporaryDirectory() as folder:
            f=ifcopenshell.file(schema='IFC2X3');path=Path(folder)/'actual.ifc';f.write(str(path));r=IFC.inspect_exchange_semantics(path)
            self.assertEqual(r['analyticalMembers'],[]);self.assertEqual(r['loadGroupCount'],0);self.assertEqual(r['calculationResults'],'NOT_PROVIDED')
    def test_ifc_opening_extended_cutter_requires_exact_host_relation(self):
        import ifcopenshell
        with tempfile.TemporaryDirectory() as folder:
            f=ifcopenshell.file(schema='IFC4');new_id=ifcopenshell.guid.new
            host=f.create_entity('IfcWall',GlobalId=new_id());opening=f.create_entity('IfcOpeningElement',GlobalId=new_id())
            relation=f.create_entity('IfcRelVoidsElement',GlobalId=new_id(),RelatingBuildingElement=host,RelatedOpeningElement=opening)
            shape_context=f.create_entity('IfcGeometricRepresentationContext',ContextType='Model',CoordinateSpaceDimension=3,
                Precision=1e-7,WorldCoordinateSystem=f.create_entity('IfcAxis2Placement3D',Location=f.create_entity('IfcCartesianPoint',Coordinates=(0.,0.,0.))))
            profile=f.create_entity('IfcRectangleProfileDef',ProfileType='AREA',XDim=.4,YDim=.9)
            solid=f.create_entity('IfcExtrudedAreaSolid',SweptArea=profile,Position=f.create_entity('IfcAxis2Placement3D',Location=f.create_entity('IfcCartesianPoint',Coordinates=(65.,60.,1.))),
                ExtrudedDirection=f.create_entity('IfcDirection',DirectionRatios=(0.,0.,1.)),Depth=.6)
            shape=f.create_entity('IfcShapeRepresentation',ContextOfItems=shape_context,RepresentationIdentifier='Body',RepresentationType='SweptSolid',Items=[solid])
            opening.Representation=f.create_entity('IfcProductDefinitionShape',Representations=[shape])
            path=Path(folder)/'real-opening.ifc';f.write(str(path))
            context={'elements':{'host':{'guid':guid(1),'kind':'Wall','bounds':[[[64.,66.],[59.85,60.15],[0.,2.]]]},
                'opening':{'guid':guid(2),'kind':'Opening','hostGuid':guid(1),'bounds':[[[64.8,65.2],[59.85,60.15],[1.,1.6]]],
                    'geometryAuthority':'TWO_ACTUAL_NATIVE_HOST_INNER_FACE_CONTOURS'}}};mapping={guid(1):host.GlobalId,guid(2):opening.GlobalId}
            row=IFC.inspect_export(path,context,mapping)['elements'][1]
            self.assertEqual(row['status'],'IFC_OPENING_HOST_CUT_BOUNDS_MATCH');self.assertAlmostEqual(row['boundsDeltaMeters'],.3)
            f.remove(relation);f.write(str(path));row=IFC.inspect_export(path,context,mapping)['elements'][1]
            self.assertEqual(row['status'],'IFC_IDENTITY_ONLY_GEOMETRY_NOT_VERIFIED')


if __name__=='__main__':unittest.main()
