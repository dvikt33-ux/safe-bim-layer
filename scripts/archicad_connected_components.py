"""Opt-in native adapters and shared facts over the retained SceneWriter.

No transport or second executor. Source-bound Details candidates remain subject
to their original commit gates; IFC/MEP membership never proves engineering.
"""
import base64
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import tarfile

import archicad_project_accelerator as A
import archicad_authored_extension as E
import archicad_authored_geometry as G
from archicad_write_cycles import hosted_roof_cycle as ROOF
from archicad_write_cycles import hosted_morph_cycle as MORPH

RUN=A.RUN
DETAILS_SHA='fbd23cbca9d306b630537679b75ff5b015f1e35a2b8470811387c137a32bdeb6'


def points_equal(left,right):
    return isinstance(right,dict) and all(RUN.close(right.get(k),left[k]) for k in ('x','y','z'))


def explicit_box_body(size):
    """Avoid the live 1.5.10 size shortcut's observed missing bottom face."""
    if set(size)!={'x','y','z'} or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in size.values()):
        raise ValueError('BOX_SIZE_NOT_FINITE_POSITIVE_XYZ')
    x,y,z=[size[k] for k in ('x','y','z')]
    vertices=[{'x':a,'y':b,'z':c} for a,b,c in
        [(0,0,0),(0,0,z),(0,y,0),(0,y,z),(x,0,0),(x,0,z),(x,y,0),(x,y,z)]]
    return {'bodyType':'Solid','edgeDefault':'HardVisible','vertices':vertices,
        'polygons':[{'vertexIds':ids,'filled':True} for ids in
            [[0,2,6,4],[0,4,5,1],[3,1,5,7],[6,2,3,7],[2,0,1,3],[4,6,7,5]]]}


def body_face_keys(body):
    """Oriented contour comparison is independent of native vertex numbering."""
    vertices=body['vertices']
    def contour(ids):
        values=[tuple(round(vertices[i][k],7) for k in ('x','y','z')) for i in ids]
        return min(tuple(values[i:]+values[:i]) for i in range(len(values)))
    return sorted((contour(p['vertexIds']),tuple(sorted(contour(h) for h in p.get('holes',[])))) for p in body['polygons'])


class NativeAdapter:
    def __init__(self,command):
        if command not in RUN.EXTENDED_WRITES:
            raise ValueError('UNKNOWN_TYPED_COMPONENT')
        self.command=command

    def before_write(self,api,params,plan):
        binding=plan.get('integrationBindings',{}).get('dependencies',{}).get('sourceDetailBinding')
        if binding is not None:
            if self.command!='CreateMorphs':raise ValueError('SOURCE_DETAIL_WRITER_COMPONENT_MISMATCH')
            from archicad_details_context import verify_source_section_binding
            verify_source_section_binding(api,binding)
            fact=details_candidate(Path(__file__).resolve().parents[1],binding['detailId'],
                {'guid':binding['hostGuid'],'kind':'Roof'})
            matched=[r for r in fact['resolvedFacts'] if r['entity']==binding['entityId'] and r['fact']['fact_id']==binding['sourceFactId']]
            if len(matched)!=1:raise ValueError('SOURCE_DETAIL_FACT_INVALIDATED')
            section={'width':matched[0]['values']['value_2']/1000,'height':matched[0]['values']['value']/1000}
            if section!=binding['sourceSectionMeters'] or binding['archiveSha256']!=DETAILS_SHA:
                raise ValueError('SOURCE_DETAIL_DIMENSION_INVALIDATED')
            data=params['morphsData'][0];body=data['body'];vertices=body['vertices']
            if {k:data.get(k) for k in binding['expectedPlacement']}!=binding['expectedPlacement']:
                raise ValueError('SOURCE_DETAIL_WRITE_PLACEMENT_MISMATCH')
            wanted={'x':binding['modelDerivedLengthMeters'],'y':section['width'],'z':section['height']}
            if body_face_keys(body)!=body_face_keys(explicit_box_body(wanted)) or any(
                    not RUN.close(max(p[k] for p in vertices)-min(p[k] for p in vertices),size) for k,size in wanted.items()):
                raise ValueError('SOURCE_DETAIL_WRITE_BODY_MISMATCH')
            if data['buildingMaterialId']['guid'].lower()!=binding['projectMaterialSelection']['expectedGuid'].lower():
                raise ValueError('SOURCE_DETAIL_WRITE_MATERIAL_MISMATCH')

    def resolve(self,step,created,plan):
        params=copy.deepcopy(step['params'])
        values=next(iter(params.values()))
        if len(values)!=1:
            raise ValueError('ONLY_ONE_ELEMENT_PER_JOURNALED_WRITE')
        data=values[0]
        if self.command=='CreateMorphs':
            if set(data)&{'size','body'} not in ({'size'},{'body'}):
                raise ValueError('MORPH_REQUIRES_EXACTLY_ONE_BODY_SPECIFICATION')
            if 'size' in data and any(type(n) not in (int,float) or not math.isfinite(n) or n<=0 for n in data['size'].values()):
                raise ValueError('MORPH_SIZE_INVALID')
        if self.command=='CreateMEPRoutingElements':
            if not all(data.get(k,0)>0 for k in ('crossSectionWidth','crossSectionHeight')):
                raise ValueError('MEP_SECTION_MUST_BE_EXPLICIT_POSITIVE')
            if not data.get('mepSystemId',{}).get('guid'):
                raise ValueError('MEP_SYSTEM_MUST_BE_PINNED')
        return params

    def floor(self,params,plan):
        if self.command in ('CreateMEPRoutingElements','CreateMEPElements'):
            # Place has no story argument. Explicitly expect the active story;
            # geometric Z must never masquerade as native home-story evidence.
            return plan['binding']['storyIndex']
        return next(iter(params.values()))[0]['floorIndex']

    def verify(self,api,guid,params,row,floor,story_level):
        expected=next(iter(params.values()))[0]
        if self.command=='CreateMEPElements':
            if row.get('floorIndex')!=floor:raise ValueError('MEP_COMPONENT_STORY_MISMATCH')
            members=[e for e in api('GetMEPElements',{}).get('elements',[]) if e['elementId']['guid'].lower()==guid.lower()]
            if len(members)>1 or (members and (members[0]['type']!=expected['type'] or members[0]['domain']!=expected.get('domain',''))):
                raise ValueError('MEP_COMPONENT_DEDICATED_TYPE_MISMATCH')
            ports=api('GetMEPPorts',{'elements':[{'elementId':{'guid':guid}}]}).get('elementPorts',[])
            if len(ports)!=1 or 'error' in ports[0] or not ports[0].get('ports'):
                raise ValueError('MEP_COMPONENT_NATIVE_PORTS_MISSING')
            normalized=G.normalize_dump(api('GetModelDumpV1',{}))
            body=next((e for e in normalized['elements'] if e['guid'].lower()==guid.lower()),None)
            if not body or not body.get('bodies'):raise ValueError('MEP_COMPONENT_NATIVE_BODY_MISSING')
            if not members and (row.get('type')!='Unknown' or body.get('nativeTypeId')!=150):
                raise ValueError('MEP_COMPONENT_OMITTED_WITHOUT_NATIVE_MEP_BODY')
            if any(p.get('domain')!=expected.get('domain','') for p in ports[0]['ports']) and expected['type']!='Equipment':
                raise ValueError('MEP_COMPONENT_ACTUAL_PORT_DOMAIN_MISMATCH')
            bounds=ROOF.bounds(body)
            if not bounds or not all(bounds[i][0]-1e-6<=expected['position'][k]<=bounds[i][1]+1e-6 for i,k in enumerate(('x','y','z'))):
                raise ValueError('MEP_COMPONENT_INSERTION_OUTSIDE_ACTUAL_BODY')
            if any(type(p.get(k)) not in (int,float) or not math.isfinite(p[k]) or p[k]<=0 for p in ports[0]['ports'] for k in ('width','height')):
                raise ValueError('MEP_COMPONENT_ACTUAL_PORT_SECTION_INVALID')
            # Installed AC29 also omits terminals from GetMEPElements. Typed
            # creation + physical MEP body/ports prove a component; exchange
            # classification must independently qualify its exact subtype.
            return 'MEP'+expected['type'] if members else 'MEPComponent'
        # Installed AC29 routing rows report Unknown/nativeType150. They are
        # accepted only alongside successful dedicated MEP geometry readback.
        wanted={'CreateRoofs':'Roof','CreateMorphs':'Morph','CreateMEPRoutingElements':'Unknown'}[self.command]
        if row.get('type')!=wanted or row.get('floorIndex')!=floor:
            raise ValueError('COMPONENT_NATIVE_TYPE_OR_STORY_MISMATCH')
        actual=row.get('details',{})
        if self.command=='CreateRoofs':
            if (actual.get('roofClass')!='SinglePlane' or actual.get('structureType')!='Basic'
                    or not RUN.close(actual.get('zCoordinate'),expected['level'])
                    or not RUN.close(actual.get('level'),expected['level']-story_level)
                    or not RUN.close(actual.get('thickness'),expected['thickness'])
                    or not RUN.close(actual.get('angle'),expected['angle'])
                    or not RUN.compare_polygon(expected['polygonCoordinates'],actual.get('polygonOutline'))
                    or actual.get('buildingMaterialId',{}).get('guid','').lower()!=expected['buildingMaterialId']['guid'].lower()):
                raise ValueError('ROOF_TYPED_READBACK_MISMATCH')
            for native,request in [('begin','begCoordinate'),('end','endCoordinate')]:
                if any(not RUN.close(actual.get('pivotLine',{}).get(native,{}).get(k),expected['pivotLine'][request][k]) for k in ('x','y')):
                    raise ValueError('ROOF_PIVOT_READBACK_MISMATCH')
            return 'Roof'
        if self.command=='CreateMorphs':
            if (not points_equal(expected['basePoint'],actual.get('origin')) or
                    actual.get('buildingMaterialId',{}).get('guid','').lower()!=expected['buildingMaterialId']['guid'].lower()):
                raise ValueError('MORPH_ORIGIN_OR_MATERIAL_MISMATCH')
            for k in ('xAxis','yAxis','zAxis'):
                if k in expected and not points_equal(expected[k],actual.get(k)):
                    raise ValueError('MORPH_TRANSFORM_READBACK_MISMATCH')
            # Reuse donor BREP parsing rather than invent a second body parser.
            faces=MORPH.native_faces_from_body(actual.get('body',{}))
            if not faces:
                raise ValueError('MORPH_BODY_READBACK_MISSING')
            if 'body' in expected and (body_face_keys(expected['body'])!=body_face_keys(actual.get('body',{}))
                    or expected['body'].get('bodyType')=='Solid' and
                        actual['body'].get('bodyType')!='Solid'):
                raise ValueError('MORPH_EXACT_BODY_OR_CLOSEDNESS_MISMATCH')
            for i,k in enumerate(('xAxis','yAxis','zAxis')):
                wanted=expected.get(k,{axis:int(i==j) for j,axis in enumerate(('x','y','z'))})
                if not points_equal(wanted,actual.get(k)):
                    raise ValueError('MORPH_DEFAULT_OR_EXPLICIT_AXES_MISMATCH')
            if 'size' in expected:
                vertices=actual.get('body',{}).get('vertices',[])
                if len(vertices)!=8 or len(faces)!=6:
                    raise ValueError('MORPH_BOX_TOPOLOGY_MISMATCH')
                if any(not RUN.close(max(v[k] for v in vertices)-min(v[k] for v in vertices),expected['size'][k]) for k in ('x','y','z')):
                    raise ValueError('MORPH_SIZE_READBACK_MISMATCH')
                axes=[actual.get(k) for k in ('xAxis','yAxis','zAxis')]
                if any(a is None for a in axes):
                    raise ValueError('MORPH_AXES_MISSING')
                normalized=G.normalize_dump(api('GetModelDumpV1',{}))
                element=next((e for e in normalized['elements'] if e['guid'].lower()==guid.lower()),None)
                if element is None:
                    raise ValueError('MORPH_NATIVE_BODY_GUID_MISSING')
                expected_cloud=[morph_api_world_point(v,expected['basePoint'],axes) for v in vertices]
                if not MORPH.cloud_compare(expected_cloud,MORPH.points_from_dump(element))[0]:
                    raise ValueError('MORPH_NATIVE_WORLD_GEOMETRY_MISMATCH')
            else:
                normalized=G.normalize_dump(api('GetModelDumpV1',{}))
                element=next((e for e in normalized['elements'] if e['guid'].lower()==guid.lower()),None)
                cloud=[morph_api_world_point(v,expected['basePoint'],[actual[k] for k in ('xAxis','yAxis','zAxis')]) for v in expected['body']['vertices']]
                if element is None or not MORPH.cloud_compare(cloud,MORPH.points_from_dump(element))[0]:
                    raise ValueError('MORPH_EXPLICIT_BODY_WORLD_COORDINATES_MISMATCH')
                if expected['body'].get('bodyType')=='Solid' and any(not b.get('closed') for b in element['bodies']):
                    raise ValueError('MORPH_NATIVE_BREP_NOT_CLOSED')
                # Memo's isClosed remains false on this installed build after a
                # successful explicit-body repair. Resultant BREP must prove
                # closure independently; keep this discrepancy visible.
                if expected['body'].get('bodyType')=='Solid':
                    from collections import Counter
                    for body in element['bodies']:
                        incidence=Counter()
                        for face in body['faces']:
                            for ring in face['contours']:
                                for i,left in enumerate(ring):
                                    incidence[tuple(sorted((left,ring[(i+1)%len(ring)])))]+=1
                        if not incidence or any(n!=2 for n in incidence.values()):
                            raise ValueError('MORPH_BREP_EDGE_INCIDENCE_NOT_CLOSED')
            return 'Morph'
        rows=api('GetMEPRoutingElements',{'elements':[{'elementId':{'guid':guid}}]}).get('routingElements')
        if not isinstance(rows,list) or len(rows)!=1 or 'error' in rows[0]:
            raise ValueError('MEP_ROUTE_READBACK_MISSING')
        route=rows[0]
        if (route.get('domain')!=expected['domain'] or attribute_guid(route.get('mepSystemId'))!=expected['mepSystemId']['guid'].lower()
                or len(route.get('polyline',[]))!=len(expected['nodeCoordinates'])
                or any(not points_equal(p,q) for p,q in zip(expected['nodeCoordinates'],route['polyline']))
                or len(route.get('segments',[]))!=len(expected['nodeCoordinates'])-1
                or len(route.get('nodes',[]))!=len(expected['nodeCoordinates'])):
            raise ValueError('MEP_ROUTE_GEOMETRY_OR_COVERAGE_MISMATCH')
        for segment in route['segments']:
            if any(not RUN.close(segment.get(k),expected[k]) for k in ('crossSectionWidth','crossSectionHeight')) or segment.get('crossSectionShape')!=expected['crossSectionShape']:
                raise ValueError('MEP_SECTION_READBACK_MISMATCH')
        if any(not points_equal(p,q.get('position')) for p,q in zip(expected['nodeCoordinates'],route['nodes'])):
            raise ValueError('MEP_NODE_POSITION_READBACK_MISMATCH')
        return 'MEPRouting'


def morph_api_world_point(point,base,axis_rows):
    """Installed Tapir xAxis/yAxis/zAxis are placement-matrix ROWS."""
    return [base[k]+sum(axis_rows[i][a]*point[a] for a in ('x','y','z')) for i,k in enumerate(('x','y','z'))]


def attribute_guid(value):
    if not isinstance(value,dict):
        raise ValueError('ATTRIBUTE_REFERENCE_INVALID')
    if set(value)=={'attributeId'}:
        value=value['attributeId']
    if not isinstance(value,dict) or set(value)!={'guid'} or not RUN._GUID.fullmatch(value['guid']):
        raise ValueError('ATTRIBUTE_GUID_INVALID')
    return value['guid'].lower()


def adapters(enabled):
    known={'roof':'CreateRoofs','morph':'CreateMorphs','mep':'CreateMEPRoutingElements','mep-component':'CreateMEPElements'}
    if set(enabled)-set(known):
        raise ValueError('UNKNOWN_OPTIONAL_MODULE')
    return {known[k]:NativeAdapter(known[k]) for k in enabled}


def details_candidate(root,detail_id,host=None):
    """Execute exact IR/entity/fact joins without extracting or executing archive."""
    release=Path(root)/'details/releases/v2.12'
    blob=base64.b64decode((release/'machine-state-v2.12.tar.gz.b64').read_bytes(),validate=False)
    if hashlib.sha256(blob).hexdigest()!=DETAILS_SHA:
        raise ValueError('DETAILS_SOURCE_HASH_MISMATCH')
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as archive:
        def rows(name):
            member=archive.getmember(name)
            if not member.isfile() or member.size>20000000:
                raise ValueError('DETAILS_MEMBER_NOT_A_BOUNDED_FILE')
            return [json.loads(line) for line in archive.extractfile(member) if line.strip()]
        selected=[r for r in rows('details_active_v2.12.jsonl') if r.get('detail',{}).get('detail_id')==detail_id]
        if len(selected)!=1:
            raise ValueError('DETAILS_ID_NOT_UNIQUE')
        facts=[r for r in rows('parameter_facts_v2.12.jsonl') if r['detail_id']==detail_id]
    candidate=selected[0];entities=json.loads(candidate['ir']['entities_json'])
    index={r['fact_id']:r for r in facts}
    resolved=[];missing=[]
    for entity in entities:
        refs=entity.get('source_parameter_fact_refs',[])
        if entity.get('required') and not refs:
            missing.append(entity['entity_id'])
        for ref in refs:
            if ref not in index:
                raise ValueError('DETAILS_DANGLING_SOURCE_FACT')
            fact=index[ref]
            if fact['source_id']!=candidate['detail']['source_id']:
                raise ValueError('DETAILS_CROSS_SOURCE_FACT')
            resolved.append({'entity':entity['entity_id'],'fact':fact,
                'values':json.loads(fact['value_json'])})
    if host is not None and (host.get('kind')!='Roof' or not RUN._GUID.fullmatch(host.get('guid',''))):
        raise ValueError('DETAILS_REQUIRES_VERIFIED_ROOF_HOST')
    return {'release':'v2.12','archiveSha256':DETAILS_SHA,'detailId':detail_id,
        'sourceId':candidate['detail']['source_id'],'host':copy.deepcopy(host),
        'entities':entities,'resolvedFacts':resolved,'missingDimensionEntities':missing,
        'sourceLocator':json.loads(candidate['detail']['source_locator_json']),
        'constructionRelations':json.loads(candidate['ir']['relations_json']),
        'status':'SOURCE_CANDIDATE_BOUND_TO_NATIVE_HOST' if host else 'SOURCE_CANDIDATE',
        'assemblyWriteAllowed':False,'assemblyGate':'SOURCE_COMMIT_FALSE_AND_UNRESOLVED_DIMENSIONS',
        'engineeringAcceptance':'NOT_VERIFIED'}


def native_context(api,source,extra_plan=None,extra_created=None):
    old=source['preflight']
    if RUN.guarded_project(api,old['storyBindings'][0])!=old['binding']:
        raise ValueError('CONNECTED_CONTEXT_TARGET_DRIFT')
    verified=E.verify_model(api,old,source['created'])
    if extra_plan:
        enabled=adapters(extra_plan['integrationBindings']['enabled'])
        for step in extra_plan['graph']['operations']:
            value=extra_created[step['id']];handler=enabled[step['command']]
            row=RUN.requested_details(api,value['guid']);floor=handler.floor(step['params'],extra_plan)
            kind=handler.verify(api,value['guid'],step['params'],row,floor,RUN.story_level_for_floor(old['storyBindings'],floor))
            if value.get('kind')!=kind or value.get('floorIndex')!=floor:
                raise ValueError('CONNECTED_LEDGER_KIND_OR_STORY_DRIFT')
            verified[step['id']]=value
    children=A.column_subelements(api,source['created'])
    raw=api('GetModelDumpV1',{});normalized=G.normalize_dump(raw)
    geometry={e['guid'].lower():e for e in normalized['elements']}
    context={'coordinateSystem':normalized['coordinateSystem'],'units':normalized['units'],
        'binding':old['binding'],'storyBindings':old['storyBindings'],'elements':{},
        'inventory':A.inventory_guids(api),'columnSegments':children}
    if context['units']!='m' or context['coordinateSystem']!='ABSOLUTE_PROJECT_XYZ':
        raise ValueError('CONNECTED_UNITS_OR_COORDINATES_MISMATCH')
    for sid,value in verified.items():
        g=value['guid'].lower();row=geometry.get(g)
        members=[row] if row else []
        members += [geometry[c] for c in children.get(g,[])]
        native_bounds=[ROOF.bounds(r) for r in members]
        native_bounds=[b for b in native_bounds if b]
        if not native_bounds and value['kind']!='MEPRouting':
            raise ValueError('CONNECTED_BODY_NOT_READABLE: '+sid)
        context['elements'][sid]={**value,'bounds':native_bounds,
            'materialBindings':row.get('materialBindings',{}) if row else {},
            'hostGuid':row.get('relationships',{}).get('hostGuid') if row else None}
        if value['kind']=='Morph':
            memo=RUN.requested_details(api,value['guid']).get('details',{}).get('body',{})
            context['elements'][sid]['closednessEvidence']={'nativeBREPClosed':all(b['closed'] for b in row['bodies']),
                'memoIsClosed':memo.get('isClosed'),'memoFlagAgreement':memo.get('isClosed')==all(b['closed'] for b in row['bodies'])}
    return context,normalized


def bind_plan(source,operations,enabled,dependencies=None):
    handlers=adapters(enabled)
    if any(s['command'] not in handlers for s in operations):
        raise ValueError('DISABLED_MODULE_OPERATION')
    plan={k:copy.deepcopy(source['preflight'][k]) for k in ('binding','storyBindings','schemaVersion','schemaSha256')}
    operations=copy.deepcopy(operations)
    for step in operations:
        if step['command']=='CreateMorphs':
            data=step['params']['morphsData'][0]
            if 'size' in data:
                if 'body' in data:
                    raise ValueError('MORPH_SIZE_AND_BODY_CONFLICT')
                data['body']=explicit_box_body(data.pop('size'))
    plan['graph']={'operations':operations}
    catalog=A.catalog_with_provenance(RUN.DEFAULT_SCENE_SCHEMA)
    checked=A.SCENE.GRAPH.compile_graph(catalog,plan['graph'],runtime_version=RUN.EXPECTED_TAPIR)
    if checked['status']!='PLAN_VALIDATED_OFFLINE':
        raise ValueError('CONNECTED_GRAPH_REFUSED: '+RUN.canonical(checked))
    plan['executionOrder']=checked['executionOrder']
    plan['metrics']={'dimensionsMeters':{'scope':'connected explicit project geometry'}}
    plan['integrationBindings']={'enabled':sorted(enabled),'retainedSourcePlanHash':source['preflight']['sourcePlanHash'],
        'retainedGuidHash':RUN.digest(source['inventory']),'dependencies':dependencies or {}}
    plan['sourcePlanHash']=RUN.native_plan_hash(plan,checked['sourcePlanHash'])
    return plan


def ifc_map(api,context):
    guids=[v['guid'] for v in context['elements'].values()]
    rows=api('GetIFCIdsOfElements',{'elements':[{'elementId':{'guid':g}} for g in guids]}).get('elementIFCIds')
    if not isinstance(rows,list) or len(rows)!=len(guids):
        raise ValueError('IFC_MAP_COVERAGE_MISMATCH')
    found={}
    for requested,row in zip(guids,rows):
        if row.get('elementId',{}).get('guid','').lower()!=requested.lower() or not isinstance(row.get('ifcId'),str) or len(row['ifcId'])!=22:
            raise ValueError('IFC_MAP_GUID_OR_ID_MISMATCH')
        if row['ifcId'] in found.values():
            raise ValueError('IFC_MAP_DUPLICATE_ID')
        found[requested.lower()]=row['ifcId']
    return found


def retained_geometry_signatures(normalized,guids):
    """Compare donor BREP and referenced Surface GUIDs, not mutable pool slots."""
    elements={e['guid'].lower():e for e in normalized['elements']}
    return {g:RUN.digest({'geometry':ROOF.geometry_signature(elements[g]),
        'faceSurfaceGuids':ROOF.face_material_guids(elements[g],normalized),
        'homeStory':elements[g]['homeStory'],'type':elements[g]['type'],
        'relationships':elements[g].get('relationships',{}),
        'materialBindings':elements[g].get('materialBindings',{})}) for g in guids}


def verify_inventory(context,source,extra_created,route_owned):
    expected=set(source['inventory'])|{v['guid'].lower() for v in extra_created.values()}|set(route_owned)
    if set(context['inventory'])!=expected:
        raise ValueError('CONNECTED_INVENTORY_HAS_UNOWNED_OR_MISSING_GUIDS')
    return sorted(expected)


def straight_route_ownership(api,plan,created,baseline):
    """Bounded single-segment proof, not a universal hierarchical MEP importer.

    Node/segment GUIDs come from RoutingElement. The one physical duct must
    independently belong to its native system and have matching endpoint ports.
    Every additional inventory GUID stays unassigned unless these checks pass.
    """
    steps=[s for s in plan['graph']['operations'] if s['command']=='CreateMEPRoutingElements']
    if len(steps)!=1:
        raise ValueError('ONLY_ONE_STRAIGHT_ROUTE_OWNERSHIP_SUPPORTED')
    step=steps[0];data=step['params']['routingElementsData'][0]
    if len(data['nodeCoordinates'])!=2:
        raise ValueError('BRANCHED_MEP_OWNERSHIP_NOT_IMPLEMENTED')
    guid=created[step['id']]['guid']
    route=api('GetMEPRoutingElements',{'elements':[{'elementId':{'guid':guid}}]})['routingElements'][0]
    direct={r['elementId']['guid'].lower() for group in ['nodes','segments'] for r in route[group]}
    if len(direct)!=3:
        raise ValueError('MEP_DIRECT_OWNER_GUIDS_DUPLICATED')
    additions=set(A.inventory_guids(api))-set(baseline)-{v['guid'].lower() for v in created.values()}-direct
    if len(additions)!=1:
        raise ValueError('MEP_PHYSICAL_GUID_DELTA_AMBIGUOUS')
    physical=next(iter(additions))
    systems=api('GetMEPDistributionSystems',{}).get('distributionSystems',[])
    membership=[s for s in systems if s.get('domain')==data['domain'] and attribute_guid(s.get('mepSystemId'))==data['mepSystemId']['guid'].lower()
        and physical in {r['elementId']['guid'].lower() for r in s.get('elements',[])}]
    if len(membership)!=1:
        raise ValueError('MEP_PHYSICAL_SYSTEM_MEMBERSHIP_MISMATCH')
    entries=api('GetMEPPorts',{'elements':[{'elementId':{'guid':physical}}]}).get('elementPorts')
    if not isinstance(entries,list) or len(entries)!=1 or len(entries[0].get('ports',[]))!=2:
        raise ValueError('MEP_PHYSICAL_PORT_COVERAGE_MISMATCH')
    ports=entries[0]['ports'];remaining=list(data['nodeCoordinates'])
    if len({p.get('portId') for p in ports})!=2:
        raise ValueError('MEP_DUPLICATED_PHYSICAL_PORTS')
    for port in ports:
        matches=[p for p in remaining if points_equal(p,port.get('position'))]
        if len(matches)!=1:
            raise ValueError('MEP_PHYSICAL_ENDPOINT_MISMATCH')
        remaining.remove(matches[0])
        if (port.get('domain')!=data['domain'] or attribute_guid(port.get('mepSystemId'))!=data['mepSystemId']['guid'].lower()
                or not RUN.close(port.get('width'),data['crossSectionWidth']) or not RUN.close(port.get('height'),data['crossSectionHeight'])
                or port.get('shape')!=data['crossSectionShape'] or type(port.get('isPhysicallyConnected')) is not bool):
            raise ValueError('MEP_PHYSICAL_PORT_ATTRIBUTES_MISMATCH')
    return {'owned':sorted(direct|{physical}),'physicalElementGuid':physical,
        'ports':ports,'physicalNetworkConnected':all(p['isPhysicallyConnected'] for p in ports),
        'evidence':'native route node/segment IDs + system membership + exact endpoint/section ports',
        'scope':'ONE_STRAIGHT_ROUTE_ONLY','engineeringAcceptance':'NOT_VERIFIED'}


def attach_physical_route(api,context,normalized,step_id,ownership):
    """Share the actual duct geometry without relabelling its container GUID."""
    logical=context['elements'][step_id]
    if logical['kind']!='MEPRouting':
        raise ValueError('PHYSICAL_ROUTE_REQUIRES_VERIFIED_CONTAINER')
    guid=ownership['physicalElementGuid']
    physical=next((e for e in normalized['elements'] if e['guid'].lower()==guid),None)
    bounds=ROOF.bounds(physical) if physical else None
    if not bounds:
        raise ValueError('MEP_PHYSICAL_NATIVE_GEOMETRY_MISSING')
    rows=api('GetIFCIdsOfElements',{'elements':[{'elementId':{'guid':guid}}]}).get('elementIFCIds')
    if not rows or len(rows)!=1 or rows[0].get('elementId',{}).get('guid','').lower()!=guid or len(rows[0].get('ifcId',''))!=22:
        raise ValueError('MEP_PHYSICAL_IFC_IDENTITY_MISSING')
    logical.update(physicalElementGuid=guid,physicalBounds=[bounds],physicalIfcId=rows[0]['ifcId'],
        physicalRelationEvidence=ownership['evidence'])
    return context


def route_ownership(api,plan,created,baseline):
    steps=[s for s in plan['graph']['operations'] if s['command']=='CreateMEPRoutingElements']
    if len(steps)==1:
        return straight_route_ownership(api,plan,created,baseline)
    import archicad_native_mep_network as M
    systems={s['params']['routingElementsData'][0]['mepSystemId']['guid'].lower() for s in steps}
    domains={s['params']['routingElementsData'][0]['domain'] for s in steps}
    if len(systems)!=1 or len(domains)!=1:raise ValueError('NETWORK_REQUIRES_ONE_PINNED_NATIVE_SYSTEM')
    network=M.read_network(api,[created[s['id']]['guid'] for s in steps],next(iter(systems)),next(iter(domains)))
    return {'owned':sorted(set(network['ownedNodeSegmentGuids'])|set(network['physicalGuids'])),
        'network':network,'scope':'DEDICATED_NATIVE_NETWORK','engineeringAcceptance':'NOT_VERIFIED'}


def main(argv=None):
    """Reusable offline/native preflight CLI; execution stays opt-in SceneWriter."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True,help='accepted local core/connected receipt')
    parser.add_argument('--intent',type=Path,required=True,help='operations, enabled, optional dependencies')
    parser.add_argument('--mode',choices=['offline','preflight','execute'],default='offline')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--state-dir',type=Path)
    parser.add_argument('--scene-id')
    parser.add_argument('--confirm-plan-hash')
    args=parser.parse_args(argv)
    record=json.loads(args.source.read_text(encoding='utf-8'))
    source=record.get('source',record)
    request=json.loads(args.intent.read_text(encoding='utf-8'))
    enabled=request['enabled'];adapters(enabled)
    new_ops=request['operations']
    if not new_ops or any(s['command'] not in adapters(enabled) for s in new_ops):
        raise ValueError('ONLY_EXPLICIT_ENABLED_NEW_COMPONENTS')
    prior_plan=record.get('connectedPlan');prior_created=record.get('connectedCreated',{})
    prior_ops=prior_plan['graph']['operations'] if prior_plan else []
    combined_enabled=sorted(set(enabled)|set(prior_plan['integrationBindings']['enabled'] if prior_plan else []))
    plan=bind_plan(source,prior_ops+new_ops,combined_enabled,dependencies={
        'request':request.get('dependencies',{}),'acceptedPrefixHash':RUN.digest(prior_created)})
    result={'status':'PLAN_VALIDATED_OFFLINE','source':source,'plan':plan,'automaticRetry':False,'modelWriteAttempts':0}
    if args.mode=='offline':
        args.output.mkdir(parents=True,exist_ok=False);A.write_json(args.output/'result.json',result)
        print(RUN.canonical({'status':result['status'],'planHash':plan['sourcePlanHash']}));return 0
    RUN.bind_isolated_writer_pln(19724)
    args.output.mkdir(parents=True,exist_ok=False)
    api=A.EvidenceAPI(A.native_transport,args.output,execute=args.mode=='execute')
    api.allowed|={'GetMEPRoutingElements','GetMEPDistributionSystems','GetMEPPorts','GetMEPElements','GetIFCIdsOfElements'}
    before_context,before=native_context(api,source,prior_plan,prior_created)
    expected_inventory=record.get('context',{}).get('inventory',source['inventory'])
    if before_context['inventory']!=expected_inventory:
        raise ValueError('ACCEPTED_WHOLE_INVENTORY_DRIFT')
    if prior_plan and any(s['command']=='CreateMEPRoutingElements' for s in prior_ops):
        ownership=route_ownership(api,prior_plan,prior_created,source['inventory'])
        verify_inventory(before_context,source,prior_created,ownership['owned'])
    plan['integrationBindings']['liveBaselineGeometryHash']=RUN.digest(retained_geometry_signatures(before,expected_inventory))
    checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(RUN.DEFAULT_SCENE_SCHEMA),plan['graph'],runtime_version=RUN.EXPECTED_TAPIR)
    plan['sourcePlanHash']=RUN.native_plan_hash(plan,checked['sourcePlanHash'])
    result.update(status='CONNECTED_NATIVE_PREFLIGHT_PASS',plan=plan,context=before_context)
    if args.mode=='execute':
        if not args.state_dir or not args.state_dir.is_dir() or not args.scene_id or args.confirm_plan_hash!=plan['sourcePlanHash']:
            raise ValueError('EXECUTE_REQUIRES_EXISTING_STATE_DIR_SCENE_ID_AND_FRESH_HASH')
        def final_check(preflight,created):
            extra={k:v for k,v in created.items() if k!='__plan__'}
            after_context,after=native_context(api,source,preflight,extra)
            owned=[]
            if any(s['command']=='CreateMEPRoutingElements' for s in preflight['graph']['operations']):
                proof=route_ownership(api,preflight,extra,source['inventory']);owned=proof['owned']
                result['routeOwnership']=proof
            verify_inventory(after_context,source,extra,owned)
            if retained_geometry_signatures(after,expected_inventory)!=retained_geometry_signatures(before,expected_inventory):
                raise ValueError('RETAINED_NATIVE_GEOMETRY_CHANGED_DURING_BATCH')
            result.update(context=after_context,connectedCreated=extra,connectedPlan=preflight)
        writer=RUN.SceneWriter(api,args.state_dir/'scene-v1-attempts.sqlite3',adapters=adapters(enabled))
        writer.required_story=plan['storyBindings'][0]
        result['writer']=writer._execute_verified_plan(plan,args.scene_id,plan['sourcePlanHash'],seeded_created=prior_created,
            approval_source='Explicit connected CLI execute with fresh native-bound hash',on_before_complete=final_check)
        result['status']=result['writer']['status']
    result['modelWriteAttempts']=api.write_attempts;result['commandCounts']=dict(api.calls)
    A.write_json(args.output/'result.json',result)
    print(RUN.canonical({'status':result['status'],'planHash':plan['sourcePlanHash'],'modelWriteAttempts':api.write_attempts}))
    return 0 if result['status'] in {'CONNECTED_NATIVE_PREFLIGHT_PASS','COMPLETE_UNSAVED'} else 2


if __name__=='__main__':
    raise SystemExit(main())
