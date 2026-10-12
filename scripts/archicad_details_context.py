"""Details v2.12 source joins and applicability over the shared native context.

All73context records are evaluated independently. Source compile gates are
retained; a geometric candidate does not certify a manufacturer assembly.
"""
import base64,copy,hashlib,io,json,tarfile
from pathlib import Path
import networkx as nx
import math
from shapely.geometry import box
import archicad_connected_components as C


class DetailsContext:
    def __init__(self,root):
        blob=base64.b64decode((Path(root)/'details/releases/v2.12/machine-state-v2.12.tar.gz.b64').read_bytes())
        if hashlib.sha256(blob).hexdigest()!=C.DETAILS_SHA:raise ValueError('DETAILS_SOURCE_HASH_MISMATCH')
        with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as t:
            def read(name,lines=False):
                member=t.getmember(name)
                if not member.isfile() or member.size>20000000:raise ValueError('DETAILS_MEMBER_INVALID')
                f=t.extractfile(member);return [json.loads(l) for l in f if l.strip()] if lines else json.load(f)
            active=read('details_active_v2.12.jsonl',True)
            self.records={r['context_detail_id']:r for r in active if 'context_detail_id' in r}
            self.detail_records={r['detail']['detail_id']:r for r in active if 'detail' in r}
            if len(self.records)!=73:raise ValueError('CONTEXT_ID_COVERAGE_OR_DUPLICATE')
            self.facts={r['fact_id']:r for r in read('parameter_facts_v2.12.jsonl',True)}
            self.sources={r['source_id']:r for r in read('sources_v2.12.json')}
            self.checks=read('SOURCE_VERIFY_FULL_v2.12.json')['representation_checks']
        for identifier,r in self.records.items():
            source_id=identifier.split('__')[0]
            source=self.sources[source_id];representation=r['source_locator']['representation']
            declared=[p for p in json.loads(source['representations_json']) if p['name']==representation]
            checked=[p for p in self.checks if p['source_id']==source_id and p['name']==representation]
            if len(declared)!=1 or len(checked)!=1 or not checked[0]['match'] or declared[0]['sha256']!=checked[0]['actual_sha256']:
                raise ValueError('CONTEXT_SOURCE_REPRESENTATION_MISMATCH')
            if r['source_locator']['page']!=r['pdf_page']:raise ValueError('CONTEXT_PAGE_MISMATCH')
            refs=set(r['inherited_fact_ids'])
            for entity in r['components']+r['context_entities']:refs.update(entity.get('source_parameter_fact_refs',[]))
            for op in r['operation_graph']:refs.update(op.get('fact_refs',[]))
            if any(ref not in self.facts or self.facts[ref]['source_id']!=source_id for ref in refs):raise ValueError('CONTEXT_DANGLING_OR_CROSS_SOURCE_FACT')

    def evaluate(self,context,product_bindings=None):
        if context['units']!='m' or context['coordinateSystem']!='ABSOLUTE_PROJECT_XYZ':raise ValueError('DETAILS_REQUIRES_NATIVE_WORLD_METRES')
        product_bindings=product_bindings or {};elements=context['elements'];graph=nx.Graph()
        for sid,e in elements.items():
            if not C.RUN._GUID.fullmatch(e['guid']):raise ValueError('DETAILS_NATIVE_GUID_INVALID')
            graph.add_node(sid,**{k:e.get(k) for k in ['guid','kind','floorIndex','hostGuid','materialBindings']})
        # Native body bounds provide a conservative candidate screen; no invented
        # exact joint or bearing-capacity inference from a bounding box.
        for sid,a in elements.items():
            for tid,b in elements.items():
                if sid>=tid:continue
                linked=a.get('hostGuid','')==b['guid'] or b.get('hostGuid','')==a['guid']
                near=any(box(x[0][0],x[1][0],x[0][1],x[1][1]).distance(box(y[0][0],y[1][0],y[0][1],y[1][1]))<.01
                    and min(x[2][1],y[2][1])-max(x[2][0],y[2][0])>=-.01 for x in a.get('bounds',[]) for y in b.get('bounds',[]))
                if linked or near:graph.add_edge(sid,tid,evidence='NATIVE_HOST' if linked else 'NATIVE_AABB_CANDIDATE')
        rows=[]
        for identifier,r in self.records.items():
            matches=[]
            for sid,wall in elements.items():
                if wall['kind']!='Wall':continue
                product=product_bindings.get(wall['guid'],{})
                material_verified=(product.get('nativeMaterialBindings')==wall.get('materialBindings') and bool(product.get('nativeMaterialBindings')))
                source_product=product.get('sourceProduct')
                reasons=[]
                if source_product not in r['source_products_in_title'] or not material_verified:reasons.append('SOURCE_PRODUCT_OR_NATIVE_MATERIAL_UNRESOLVED')
                neighbors=list(graph.neighbors(sid))
                wanted={e['preferred_archicad_tool'] for e in r['context_entities'] if e.get('required')}
                bound=[t for t in neighbors if elements[t]['kind'] in wanted]
                if wanted and not all(any(elements[t]['kind']==kind for t in bound) for kind in wanted):reasons.append('REQUIRED_GEOMETRIC_CONTEXT_MISSING')
                matches.append({'hostGuid':wall['guid'],'hostStepId':sid,'floorIndex':wall['floorIndex'],
                    'nativeBoundsMeters':wall['bounds'],'nativeMaterialBindings':wall.get('materialBindings',{}),
                    'contextGuids':[elements[t]['guid'] for t in bound],'sourceProduct':source_product,
                    'applicability':'CANDIDATE_CONTEXT_MATCH' if not reasons else 'NOT_APPLICABLE_OR_UNRESOLVED','reasons':reasons})
            refs=set(r['inherited_fact_ids'])
            for e in r['components']+r['context_entities']:refs.update(e.get('source_parameter_fact_refs',[]))
            for op in r['operation_graph']:refs.update(op.get('fact_refs',[]))
            rows.append({'detailId':identifier,'sourceId':identifier.split('__')[0],'sourceLocator':r['source_locator'],
                'junctionType':r['junction_type'],'wallTypeId':r['wall_type_id'],'bindings':matches,
                'resolvedFacts':[{'factId':ref,'unit':self.facts[ref]['normalized_unit'],'values':json.loads(self.facts[ref]['value_json'])} for ref in sorted(refs)],
                'relations':r['relations'],'operationGraph':r['operation_graph'],'compileBlockers':list(r['compile_blockers']),
                'assemblyWriteAllowed':False,'sourceCommitAllowed':r['commit_allowed'],'engineeringAcceptance':'NOT_VERIFIED'})
        return {'schema':'APA_DETAILS_NATIVE_CONTEXT_V1','archiveSha256':C.DETAILS_SHA,'contextDetailCount':len(rows),
            'nativeContextHash':C.RUN.digest(context),'nativeGraphNodes':graph.number_of_nodes(),'nativeGraphEdges':graph.number_of_edges(),
            'details':rows,'scope':'Source-verified applicability/host/material/geometry/fact exchange; exact assembly source gates preserved',
            'engineeringAcceptance':'NOT_VERIFIED'}

    def exchange(self,result,detail_id,host_guid):
        rows=[r for r in result['details'] if r['detailId']==detail_id]
        if len(rows)!=1:raise ValueError('DETAIL_ID_NOT_UNIQUE')
        row=copy.deepcopy(rows[0]);bindings=[b for b in row['bindings'] if b['hostGuid']==host_guid]
        if len(bindings)!=1:raise ValueError('DETAIL_HOST_NOT_VERIFIED')
        row['bindings']=bindings;return row


def required_junction_matrix(context,evaluated):
    """Model-derived families for existing A04.S01-S03, without source approval."""
    kinds={};rows=[]
    for sid,e in context['elements'].items():kinds.setdefault(e['kind'],[]).append(e['guid'])
    families={'openings':('Wall',('Opening','Window','Door')),'wall_floor':('Wall',('Slab',)),
        'wall_roof':('Wall',('Roof',)),'wall_intersections':('Wall',('Wall',)),
        'mep_penetrations':('Wall',('MEPRouting',))}
    for family,(host_kind,neighbors) in families.items():
        hosts=kinds.get(host_kind,[]);targets=[g for k in neighbors for g in kinds.get(k,[])]
        junctions={'openings':{'wall_floor_opening_section','balcony_door_or_balcony_slab','bay_window'},
            'wall_floor':{'wall_floor_opening_section','foundation_slab_with_or_without_grade_beam'},
            'wall_roof':{'pitched_roof_wall_junction','flat_roof_parapet'},
            'wall_intersections':{'external_corner','internal_corner','exterior_internal_wall_intersection','internal_loadbearing_wall'},
            'mep_penetrations':{'airduct_masonry_bond'}}
        evidence=[{'detailId':d['detailId'],'sourceId':d['sourceId'],'sourceLocator':d['sourceLocator'],
            'candidateHostGuids':[b['hostGuid'] for b in d['bindings'] if b['applicability']=='CANDIDATE_CONTEXT_MATCH'],
            'sourceBlockers':d['compileBlockers']} for d in evaluated['details'] if d['junctionType'] in junctions[family] and any(
                b['hostGuid'] in hosts for b in d['bindings'])]
        rows.append({'family':family,'hostGuids':hosts,'contextGuids':targets,'sourceCandidates':evidence,
            'status':'MODEL_FAMILY_REQUIRES_QUALIFIED_SOURCE_AND_JUNCTION_GEOMETRY' if hosts and targets else 'NOT_PRESENT_IN_MODEL',
            'engineeringAcceptance':'NOT_VERIFIED'})
    return {'schema':'APA_REQUIRED_JUNCTION_MATRIX_V1','existingTasks':['APA-P70.A04.S01','APA-P70.A04.S02','APA-P70.A04.S03'],
        'nativeContextHash':C.RUN.digest(context),'families':rows,'coverageScope':'Bounded accepted model; bounding boxes are candidate evidence only'}


def native_junction_coverage(context,native,details,collision_pairs=()):
    """Join real host/material/body facts to all model junction families.

    Retained Shapely BREP surface analysis proves planar surface coincidence;
    native collision pairs independently identify volume overlap. Logical host
    links do not imply either physical contact or engineering acceptance.
    """
    import itertools
    bodies={e['guid'].lower():e for e in native['elements']}
    if native.get('units')!='m' or native.get('coordinateSystem')!='ABSOLUTE_PROJECT_XYZ':
        raise ValueError('JUNCTION_REQUIRES_NATIVE_WORLD_METRES')
    entries={e['guid'].lower():dict(e,stepId=sid) for sid,e in context['elements'].items()
             if not e['kind'].startswith('MEP') and e['kind']!='Opening'}
    collisions={tuple(sorted(g.lower() for g in pair)) for pair in collision_pairs}
    definitions={
        'wall_floor':({'Wall'},{'Slab'}),
        'wall_window':({'Wall'},{'Window','Door'}),
        'wall_roof':({'Wall'},{'Roof'}),
        'roof_members_and_abutments':({'Roof','Morph','Beam'},{'Morph','Beam'}),
        'cladding_structure':({'CurtainWall','Cladding'},{'Wall','Column','Roof'}),
        'wall_intersections_and_ties':({'Wall'},{'Wall'}),
        'column_floor':({'Column'},{'Slab'}),
    }
    source_types={
        'wall_floor':{'wall_floor_opening_section','foundation_slab_with_or_without_grade_beam'},
        'wall_window':{'wall_floor_opening_section','window_opening','bay_window'},
        'wall_roof':{'pitched_roof_wall_junction','flat_roof_parapet'},
        'roof_members_and_abutments':{'ridge','eaves_with_overhang','gable_end','sheet_metal_profile'},
        'cladding_structure':{'facade_plinth','external_corner','window_opening'},
        'wall_intersections_and_ties':{'internal_loadbearing_wall','external_corner','exterior_internal_wall_intersection'},
        'column_floor':{'foundation_slab_with_or_without_grade_beam'},
    }
    sources=[]
    evaluated=details.evaluate(context)
    for d in evaluated['details']:
        sources.append({'detailId':d['detailId'],'sourceId':d['sourceId'],'junctionType':d['junctionType'],
            'sourceLocator':d['sourceLocator'],'compileBlockers':d['compileBlockers'],
            'sourceCommitAllowed':d['sourceCommitAllowed'],'assemblyWriteAllowed':False,
            'nativeMaterialMatchCount':sum(b['applicability']=='CANDIDATE_CONTEXT_MATCH' for b in d['bindings'])})
    for r in details.detail_records.values():
        d=r['detail'];sources.append({'detailId':d['detail_id'],'sourceId':d['source_id'],
            'junctionType':d['junction_type'],'sourceLocator':json.loads(d['source_locator_json']),
            'sourceCommitAllowed':bool(r['ir']['commit_allowed']),'assemblyWriteAllowed':False,
            'compileBlockers':json.loads(r['ir']['preconditions_json']).get('source_blockers',[])})
    graph=nx.Graph();rows=[]
    for g,e in entries.items():graph.add_node(g,kind=e['kind'],floorIndex=e['floorIndex'])
    for family,(left,right) in definitions.items():
        pairs=[]
        for a,b in itertools.combinations(entries,2):
            ea,eb=entries[a],entries[b]
            if not ((ea['kind'] in left and eb['kind'] in right) or (eb['kind'] in left and ea['kind'] in right)):continue
            pair=tuple(sorted((a,b)))
            explicit_host=(ea.get('hostGuid','') or '').lower()==b or (eb.get('hostGuid','') or '').lower()==a
            near=any(all(min(x[k][1],y[k][1])-max(x[k][0],y[k][0])>=-1e-6 for k in range(3))
                     for x in ea.get('bounds',[]) for y in eb.get('bounds',[]))
            if family=='wall_roof' and ea['floorIndex']==eb['floorIndex']:
                # Upper-storey walls still require a roof junction even where
                # the actual untrimmed wall stops below the sloping roof.
                near=near or any(all(min(x[k][1],y[k][1])-max(x[k][0],y[k][0])>=-1e-6 for k in range(2))
                                for x in ea.get('bounds',[]) for y in eb.get('bounds',[]))
            if family=='roof_members_and_abutments' and not (ea['kind']=='Roof' or eb['kind']=='Roof' or
                    any(entries.get((e.get('hostGuid') or '').lower(),{}).get('kind')=='Roof' for e in (ea,eb))):continue
            if not (explicit_host or near):continue
            owners={}
            for g in pair:
                children=next((v for slot in ('columnSegments','beamSegments') for k,v in context.get(slot,{}).items() if k.lower()==g),[])
                if bodies.get(g,{}).get('bodies') or not children:owners[g]=g
                for child in children:owners[child.lower()]=g
            area=None;reason=None
            try:
                if any(g not in bodies or not bodies[g].get('bodies') for g in owners):raise ValueError('NATIVE_BODY_NOT_AVAILABLE')
                contacts=C.G.shared_surfaces(bodies,owners)
                area=sum(c['sharedAreaSquareMeters'] for c in contacts if tuple(c['guids'])==pair)
            except (ValueError,KeyError,IndexError) as exc:reason=str(exc)
            intersection=pair in collisions
            physical='SURFACE_CONTACT' if area is not None and area>1e-8 else ('VOLUME_INTERSECTION' if intersection else 'NOT_VERIFIED' if reason else 'NO_SHARED_SURFACE')
            if intersection and physical=='SURFACE_CONTACT':physical='SHARED_SURFACE_AND_VOLUME_INTERSECTION'
            relation={'guids':list(pair),'elements':[{'guid':g,'kind':entries[g]['kind'],'floorIndex':entries[g]['floorIndex'],
                'boundsMeters':entries[g]['bounds'],'materialBindings':entries[g].get('materialBindings',{})} for g in pair],
                'logicalBinding':explicit_host,'logicalBindingAuthority':'CONTEXT_HOST; NATIVE_RELATION_REQUIRES_READBACK' if explicit_host else None,
                'sharedAreaSquareMeters':area,'physicalRelation':physical,'nativeVolumeIntersection':intersection,
                'contactAnalysisLimitation':reason,'engineeringAcceptance':'NOT_VERIFIED','family':family}
            pairs.append(relation);graph.add_edge(a,b,family=family,physicalRelation=physical)
        candidates=[s for s in sources if s['junctionType'] in source_types[family]]
        rows.append({'family':family,'status':'MODEL_CONTACTS_CLASSIFIED_WITH_SOURCE_GAPS' if pairs else 'NOT_PRESENT_OR_NO_BOUND_INTERFACE',
            'junctions':pairs,'sourceCandidates':candidates,
            'sourceMaterialQualification':'No product-name equivalence to native structural concrete/timber is inferred',
            'gaps':['Construction layer/fastener/grade/load capacity require source and engineering qualification'],
            'engineeringAcceptance':'NOT_VERIFIED'})
    openings=[]
    from archicad_native_operations import opening_hole_bounds
    for e in context['elements'].values():
        if e['kind']!='Opening':continue
        g=e['guid'].lower();host=(e.get('hostGuid') or '').lower();row={'guid':g,'hostGuid':host,
            'homeStory':e['floorIndex'],'boundsMeters':e['bounds'],'engineeringAcceptance':'NOT_VERIFIED',
            'status':'NOT_VERIFIED','sourceCandidates':[s for s in sources if s['junctionType'] in source_types['wall_window']]}
        try:
            bounds=e['bounds'][0];hb=entries[host]['bounds'][0]
            horizontal=max(range(2),key=lambda k:hb[k][1]-hb[k][0])
            expected={'width':bounds[horizontal][1]-bounds[horizontal][0],
                'height':bounds[2][1]-bounds[2][0],
                'basePoint':{'x':sum(bounds[0])/2,'y':sum(bounds[1])/2,'z':bounds[2][0]}}
            row['nativeHoleBoundsMeters']=opening_hole_bounds({'native':bodies[host]},expected)
            row.update(status='ACTUAL_HOST_INNER_CONTOURS_PASS',geometryAuthority='TWO_NATIVE_HOST_FACE_HOLES; OPENING_PROXY_HAS_NO_SOLID')
        except (ValueError,KeyError,IndexError) as exc:row['limitation']=str(exc)
        openings.append(row)
    return {'schema':'APA_NATIVE_JUNCTION_COVERAGE_V1','nativeContextHash':C.RUN.digest(context),
        'nativeBodyHash':C.RUN.digest(native),'archiveSha256':C.DETAILS_SHA,'contextDetailCount':len(evaluated['details']),
        'sourceDetailCount':len(details.detail_records),'families':rows,'graphNodes':graph.number_of_nodes(),'graphEdges':graph.number_of_edges(),
        'sourceApprovedFullAssemblyCount':sum(s['sourceCommitAllowed'] for s in sources),
        'hostedOpenings':openings,
        'armopoyasAndFasteners':{'status':'NOT_VERIFIED','reason':'Existing concrete geometry does not establish reinforcement, anchoring or fastener schedules',
            'sourceCandidates':[s for s in sources if any(word in s['junctionType'] for word in ('armop','reinfor','anchor','tie'))]},
        'coverageScope':'All required families in accepted native context, plus actual wall/column interfaces. Surface contact and native intersection are separate. No full-family or engineering approval.'}


def qualify_native_junctions(coverage,support_readbacks=()):
    """Grade actual interfaces without promoting contact to assembly approval.

    Documentation applies only to independently verified source support
    sub-junctions whose exact native pair and area agree with this coverage.
    These records are verification outputs, never an engineering certificate.
    """
    if coverage.get('schema')!='APA_NATIVE_JUNCTION_COVERAGE_V1':
        raise ValueError('JUNCTION_QUALIFICATION_REQUIRES_NATIVE_COVERAGE')
    verified={}
    for proof in support_readbacks:
        pair=tuple(sorted((proof['newGuid'].lower(),proof['counterpartGuid'].lower())))
        if (proof.get('status')!='LIVE_SOURCE_SUPPORT_CONTACT_PASS' or len(set(pair))!=2
                or proof.get('physicalContact')!='PASS_GEOMETRY'
                or proof.get('nativeVolumeCollision',{}).get('collisions')!=[]
                or not proof.get('sourceDetailId') or not proof.get('sourceRelation')
                or proof.get('completeManufacturerAssembly')!='NOT_VERIFIED'
                or proof.get('engineeringAcceptance')!='NOT_VERIFIED' or pair in verified):
            raise ValueError('JUNCTION_SUPPORT_PROOF_INVALID_OR_DUPLICATE')
        verified[pair]=proof
    families=[];matched=set();counts={'PASS_GEOMETRY':0,'PASS_DOCUMENTED':0,'PASS_ENGINEERING':0,'NOT_VERIFIED':0}
    for family in coverage['families']:
        rows=[]
        for j in family['junctions']:
            pair=tuple(sorted(g.lower() for g in j['guids']))
            area=j.get('sharedAreaSquareMeters')
            geometry=(type(area) in (int,float) and math.isfinite(area) and area>1e-8
                and j['physicalRelation']=='SURFACE_CONTACT' and not j['nativeVolumeIntersection']
                and not j['contactAnalysisLimitation'])
            documented=False;proof=verified.get(pair)
            if proof:
                if not geometry or not C.RUN.close(area,proof['sharedAreaSquareMeters'],1e-6):
                    raise ValueError('JUNCTION_SUPPORT_PROOF_COVERAGE_MISMATCH')
                documented=True;matched.add(pair)
            status='PASS_DOCUMENTED' if documented else 'PASS_GEOMETRY' if geometry else 'NOT_VERIFIED'
            counts[status]+=1
            rows.append({'guids':list(pair),'status':status,'geometry':'PASS_GEOMETRY' if geometry else 'NOT_VERIFIED',
                'documentation':'PASS_DOCUMENTED' if documented else 'NOT_VERIFIED',
                'engineering':'NOT_VERIFIED','sharedAreaSquareMeters':area,
                'physicalRelation':j['physicalRelation'],'nativeVolumeIntersection':j['nativeVolumeIntersection'],
                'contactAnalysisLimitation':j['contactAnalysisLimitation'],
                'sourceDetailId':proof['sourceDetailId'] if proof else None,
                'sourceRelation':proof['sourceRelation'] if proof else None,
                'scope':'SOURCE_SUPPORT_SUBJUNCTION' if documented else 'ACTUAL_INTERFACE_ONLY',
                'completeAssembly':'NOT_VERIFIED','elements':j['elements']})
        families.append({'family':family['family'],'junctions':rows,
            'completeFamily':'NOT_VERIFIED','engineering':'NOT_VERIFIED',
            'presence':family['status'],'sourceCandidates':family['sourceCandidates'],'gaps':family['gaps']})
    if matched!=set(verified):raise ValueError('JUNCTION_SUPPORT_PROOF_PAIR_NOT_IN_COVERAGE')
    openings=[dict(o,geometry='PASS_GEOMETRY' if o['status']=='ACTUAL_HOST_INNER_CONTOURS_PASS' else 'NOT_VERIFIED',
        documentation='NOT_VERIFIED',engineering='NOT_VERIFIED',completeAssembly='NOT_VERIFIED') for o in coverage['hostedOpenings']]
    return {'schema':'APA_NATIVE_JUNCTION_QUALIFICATION_V1','families':families,'hostedOpenings':openings,
        'counts':counts,'archiveSha256':coverage['archiveSha256'],'nativeContextHash':coverage['nativeContextHash'],
        'nativeBodyHash':coverage['nativeBodyHash'],'sourceApprovedFullAssemblyCount':coverage['sourceApprovedFullAssemblyCount'],
        'armopoyasAndFasteners':coverage['armopoyasAndFasteners'],
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED','completeFamilies':'NOT_VERIFIED',
        'scope':'Native face contact, documented bounded support and volume intersection are separate; no family or engineering promotion'}


def prepare_source_section(root,source,context,native,host_guid,entity_id,material_selection,placement_y=None):
    """Two confirmed ARMO cross sections as independent geometric parts.

    Length and placement come from a measured native planar roof. The material
    is explicitly project-selected, with no manufacturer material approval.
    Missing assembly dimensions remain blocked. This returns the existing
    SceneWriter graph; execution must reacquire host/material and target.
    """
    from shapely.geometry import Polygon,Point
    hosts=[e for e in context['elements'].values() if e['guid'].lower()==host_guid.lower()]
    if len(hosts)!=1 or hosts[0]['kind']!='Roof':raise ValueError('DETAIL_PART_REQUIRES_UNIQUE_NATIVE_ROOF')
    if (set(material_selection)!={'kind','name','expectedGuid'} or material_selection['kind']!='BuildingMaterial'
            or not material_selection['name'] or not C.RUN._GUID.fullmatch(material_selection['expectedGuid'])):
        raise ValueError('DETAIL_PART_TYPED_MATERIAL_SELECTION_REQUIRED')
    material_guid=material_selection['expectedGuid']
    host=hosts[0];candidate=C.details_candidate(root,'ARMO_SELFLOCK_ROOF__P0003',host)
    selected=[r for r in candidate['resolvedFacts'] if r['entity']==entity_id]
    if len(selected)!=1 or selected[0]['fact']['fact_kind']!='cross_section' or selected[0]['fact']['normalized_unit']!='mm':
        raise ValueError('DETAIL_PART_SOURCE_CROSS_SECTION_NOT_UNIQUE')
    fact=selected[0];width= fact['values']['value_2']/1000;height=fact['values']['value']/1000
    if any(type(v) not in (float,int) or not math.isfinite(v) or v<=0 for v in (width,height)):
        raise ValueError('DETAIL_PART_DIMENSION_INVALID')
    bodies=[e for e in native['elements'] if e['guid'].lower()==host_guid.lower()]
    if len(bodies)!=1:raise ValueError('DETAIL_PART_HOST_BODY_MISSING')
    body=bodies[0];b=C.ROOF.bounds(body)
    if placement_y is None:
        candidates=[(b[1][0]+b[1][1])/2,b[1][0]+(b[1][1]-b[1][0])/4,b[1][0]+3*(b[1][1]-b[1][0])/4]
        rejected=[]
        for y in candidates:
            part=prepare_source_section(root,source,context,native,host_guid,entity_id,material_selection,y)
            data=part['plan']['graph']['operations'][0]['params']['morphsData'][0]
            cloud=[C.morph_api_world_point(p,data['basePoint'],[data[k] for k in ('xAxis','yAxis','zAxis')]) for p in data['body']['vertices']]
            bounds=[(min(p[k] for p in cloud),max(p[k] for p in cloud)) for k in range(3)]
            blockers=[sid for sid,e in context['elements'].items() if e['guid'].lower()!=host_guid.lower() and
                any(all(min(a[1],box[1])-max(a[0],box[0])>1e-7 for a,box in zip(bounds,b)) for b in e.get('bounds',[]))]
            if not blockers:
                part['placementCandidates']={'selectedY':y,'rejected':rejected,'authority':'Explicit native roof quarter-span candidates; exact native collision readback still required'}
                return part
            rejected.append({'y':y,'blockedBy':blockers})
        raise ValueError('DETAIL_PART_NO_UNOBSTRUCTED_NATIVE_ROOF_CANDIDATE')
    if type(placement_y) not in (int,float) or not math.isfinite(placement_y):raise ValueError('DETAIL_PART_PLACEMENT_Y_INVALID')
    y=placement_y
    planes=[]
    for solid in body['bodies']:
        if solid['curved']:raise ValueError('DETAIL_PART_CURVED_ROOF_NOT_SUPPORTED')
        for face in solid['faces']:
            points=[solid['vertices'][i] for i in face['vertices']]
            if len(points)<3:continue
            a,v,w=points[0],points[1],points[2]
            n=[(v[(k+1)%3]-a[(k+1)%3])*(w[(k+2)%3]-a[(k+2)%3])-(v[(k+2)%3]-a[(k+2)%3])*(w[(k+1)%3]-a[(k+1)%3]) for k in range(3)]
            if abs(n[2])<1e-8:continue
            if any(abs(sum(n[k]*(p[k]-a[k]) for k in range(3)))>1e-6 for p in points):continue
            polygon=Polygon([(p[0],p[1]) for p in points], [[tuple(solid['vertices'][i][:2]) for i in ring] for ring in face.get('holes',[])])
            if not polygon.is_valid:continue
            if all(polygon.covers(Point(x,yy)) for x in (b[0][0],b[0][1]) for yy in (y-width/2,y+width/2)):
                z=lambda x,yy,a=a,n=n:a[2]-(n[0]*(x-a[0])+n[1]*(yy-a[1]))/n[2]
                planes.append((z((b[0][0]+b[0][1])/2,y),z,n))
    if not planes:raise ValueError('DETAIL_PART_NATIVE_FACE_FOOTPRINT_NOT_VERIFIED')
    _,z,n=min(planes,key=lambda p:p[0]);slope=-n[1]/n[2]
    # Bounded horizontal-x batten. Do not pretend this is rafter-following c5.
    if entity_id!='c4' or abs(n[0]/n[2])>1e-8:raise ValueError('DETAIL_PART_ORIENTATION_RELATION_UNSUPPORTED')
    tangent={'x':0.,'y':1/math.sqrt(1+slope*slope),'z':slope/math.sqrt(1+slope*slope)}
    normal={'x':0.,'y':-tangent['z'],'z':tangent['y']}
    base={'x':b[0][0],'y':y-tangent['y']*width/2-normal['y']*height,
          'z':z(b[0][0],y)-tangent['z']*width/2-normal['z']*height}
    # Tapir stores these fields as matrix rows. Transpose the desired local
    # basis so actual BREP rises with the measured roof, not against its slope.
    data={'floorIndex':host['floorIndex'],'basePoint':base,'xAxis':{'x':1.,'y':0.,'z':0.},
          'yAxis':{'x':0.,'y':tangent['y'],'z':normal['y']},'zAxis':{'x':0.,'y':tangent['z'],'z':normal['z']},
          'body':C.explicit_box_body({'x':b[0][1]-b[0][0],'y':width,'z':height}),'buildingMaterialId':{'guid':material_guid}}
    binding={'detailId':candidate['detailId'],'entityId':entity_id,'sourceFactId':fact['fact']['fact_id'],
        'sourceLocator':candidate['sourceLocator'],'archiveSha256':candidate['archiveSha256'],'hostGuid':host['guid'],
        'hostGeometryHash':C.RUN.digest(C.ROOF.geometry_signature(body)),'hostMaterialBindings':host['materialBindings'],
        'hostHomeStory':body['homeStory'],'expectedPlacement':{k:data[k] for k in ('floorIndex','basePoint','xAxis','yAxis','zAxis')},
        'projectMaterialSelection':dict(material_selection),'sourceSectionMeters':{'width':width,'height':height},
        'modelDerivedLengthMeters':b[0][1]-b[0][0],'assemblyWriteAllowed':False,
        'scope':'INDEPENDENT_SOURCE_SECTION_PART; NOT_COMPLETE_MANUFACTURER_ASSEMBLY',
        'materialAcceptance':'PROJECT_SELECTION_REQUIRES_FRESH_NATIVE_RESOLVE; SOURCE_MATERIAL_NOT_SPECIFIED',
        'engineeringAcceptance':'NOT_VERIFIED','missingAssemblyDimensionEntities':candidate['missingDimensionEntities']}
    plan=C.bind_plan(source,[{'id':'source-section-'+entity_id,'command':'CreateMorphs','params':{'morphsData':[data]}}],['morph'],{'sourceDetailBinding':binding})
    return {'status':'OFFLINE_SOURCE_SECTION_GRAPH_PREPARED','binding':binding,'plan':plan,'nativeWrites':0,
        'livePrerequisites':['exact PLN/port/process/Tapir/journal','baseline59 preservation','fresh host geometry/material match','fresh project material resolve']}


def verify_source_section_binding(api,binding):
    from archicad_native_operations import element_body
    body=element_body(api,binding['hostGuid'])
    if C.RUN.digest(C.ROOF.geometry_signature(body['native']))!=binding['hostGeometryHash']:
        raise ValueError('DETAIL_PART_HOST_GEOMETRY_INVALIDATED')
    if body['native'].get('materialBindings',{})!=binding['hostMaterialBindings']:
        raise ValueError('DETAIL_PART_HOST_MATERIAL_INVALIDATED')
    if body['native'].get('homeStory')!=binding['hostHomeStory']:raise ValueError('DETAIL_PART_HOST_STORY_INVALIDATED')
    from archicad_native_material_selection import resolve
    selection=binding['projectMaterialSelection']
    resolve(api,selection['kind'],selection['name'],selection['expectedGuid'])
    for dependency in binding.get('nativeDependencyBodies',[]):
        current=element_body(api,dependency['guid'])['native']
        if (C.RUN.digest(C.ROOF.geometry_signature(current))!=dependency['geometryHash'] or
                current.get('materialBindings',{})!=dependency['materialBindings'] or
                current.get('homeStory')!=dependency['homeStory']):
            raise ValueError('JUNCTION_NATIVE_DEPENDENCY_INVALIDATED')
    return {'status':'DETAIL_PART_HOST_BINDING_PASS','hostGuid':binding['hostGuid']}


def prepare_counterbatten_junction(root,source,context,native,batten_guid,end_wall_guid):
    """One source-dimensioned support junction on the existing native batten.

    The new50x50mm member follows the measured roof/batten slope. Its start is
    the actual batten underside edge and its end is the actual upper-wall inner
    face. No invented member length, fastening schedule or full-assembly gate.
    """
    entries={e['guid'].lower():e for e in context['elements'].values()}
    bodies={e['guid'].lower():e for e in native['elements']}
    batten=entries[batten_guid.lower()];wall=entries[end_wall_guid.lower()]
    roof=entries[(batten.get('hostGuid') or '').lower()]
    if batten['kind'] not in ('Morph','Beam') or roof['kind']!='Roof' or wall['kind']!='Wall' or wall['floorIndex']!=roof['floorIndex']:
        raise ValueError('COUNTERBATTEN_REQUIRES_ACCEPTED_BATTEN_ROOF_UPPER_WALL')
    candidate=C.details_candidate(root,'ARMO_SELFLOCK_ROOF__P0003',roof)
    if not any(r['relation']=='battens_supported_by_counterbattens' and r['battens_position']==4 and r['counterbattens_position']==5
               for r in candidate['constructionRelations']):raise ValueError('COUNTERBATTEN_SOURCE_RELATION_MISSING')
    facts={r['entity']:r for r in candidate['resolvedFacts']}
    if any(facts[k]['fact']['fact_kind']!='cross_section' or facts[k]['fact']['normalized_unit']!='mm' for k in ('c4','c5')):
        raise ValueError('COUNTERBATTEN_SOURCE_DIMENSIONS_NOT_CONFIRMED')
    width=facts['c5']['values']['value_2']/1000;height=facts['c5']['values']['value']/1000
    from shapely.geometry import Polygon
    planes=[];body=bodies[batten_guid.lower()]
    segment_dependencies=[]
    if batten['kind']=='Beam':
        segments=[e for e in bodies.values() if e.get('relationships',{}).get('hostGuid','').lower()==batten_guid.lower()]
        if not segments or any(e['type']!='BeamSegment' or e['homeStory']!=body['homeStory'] or not e.get('bodies') for e in segments):
            raise ValueError('COUNTERBATTEN_NATIVE_BEAM_SEGMENTS_NOT_PROVEN')
        material=segments[0]['materialBindings']
        if any(e['materialBindings']!=material for e in segments):raise ValueError('COUNTERBATTEN_MULTIMATERIAL_BEAM_UNSUPPORTED')
        body={**body,'bodies':[s for e in segments for s in e['bodies']],'materialBindings':material}
        segment_dependencies=segments
    for solid in body['bodies']:
        for face in solid['faces']:
            points=[solid['vertices'][i] for i in face['vertices']]
            if len(points)<3:continue
            a,v,w=points[:3]
            n=[(v[(k+1)%3]-a[(k+1)%3])*(w[(k+2)%3]-a[(k+2)%3])-(v[(k+2)%3]-a[(k+2)%3])*(w[(k+1)%3]-a[(k+1)%3]) for k in range(3)]
            if abs(n[2])<1e-8 or abs(n[0]/n[2])>1e-8:continue
            if any(abs(sum(n[k]*(p[k]-a[k]) for k in range(3)))>1e-6 for p in points):continue
            slope=-n[1]/n[2];intercept=a[2]-slope*a[1]
            polygon=Polygon([(p[0],p[1]) for p in points])
            if not polygon.is_valid or face.get('holes'):raise ValueError('COUNTERBATTEN_SUPPORT_FACE_UNSUPPORTED')
            area=polygon.area*math.sqrt(sum(v*v for v in n))/abs(n[2])
            planes.append((intercept,slope,points,area))
    largest=max((p[3] for p in planes),default=0)
    planes=[p for p in planes if C.RUN.close(p[3],largest)]
    if len(planes)!=2:raise ValueError('COUNTERBATTEN_BATTEN_UNDERSIDE_NOT_UNIQUE')
    intercept,slope,face,_=min(planes,key=lambda p:p[0])
    if not C.RUN.close(planes[0][1],planes[1][1]):raise ValueError('COUNTERBATTEN_BATTEN_NONPARALLEL_FACES')
    cosine=1/math.sqrt(1+slope*slope);sine=slope*cosine
    cloud=[p for solid in body['bodies'] for p in solid['vertices']]
    tangent=[cosine*p[1]+sine*p[2] for p in cloud];normal=[-sine*p[1]+cosine*p[2] for p in cloud]
    if not C.RUN.close(max(tangent)-min(tangent),facts['c4']['values']['value_2']/1000) or not C.RUN.close(max(normal)-min(normal),facts['c4']['values']['value']/1000):
        raise ValueError('COUNTERBATTEN_ACCEPTED_BATTEN_SECTION_DRIFT')
    rb=C.ROOF.bounds(bodies[roof['guid'].lower()]);wb=C.ROOF.bounds(bodies[wall['guid'].lower()])
    x=sum(rb[0])/2;start=min(p[1] for p in face);end=wb[1][0]
    if not (wb[0][0]<=x<=wb[0][1] and min(p[0] for p in face)<x-width/2<x+width/2<max(p[0] for p in face)
            and end>max(p[1] for p in face)):raise ValueError('COUNTERBATTEN_MODEL_SPAN_NOT_SUPPORTED')
    length=(end-start)/cosine
    material=body['materialBindings']['buildingMaterial']
    selection={'kind':'BuildingMaterial','name':material['name'],'expectedGuid':material['guid']}
    data={'floorIndex':roof['floorIndex'],'basePoint':{'x':x+width/2,'y':start+sine*height,'z':intercept+slope*start-cosine*height},
        'xAxis':{'x':0.,'y':-1.,'z':0.},'yAxis':{'x':cosine,'y':0.,'z':-sine},'zAxis':{'x':sine,'y':0.,'z':cosine},
        'body':C.explicit_box_body({'x':length,'y':width,'z':height}),'buildingMaterialId':{'guid':material['guid']}}
    binding={'detailId':candidate['detailId'],'entityId':'c5','sourceFactId':facts['c5']['fact']['fact_id'],
        'sourceLocator':candidate['sourceLocator'],'archiveSha256':candidate['archiveSha256'],'hostGuid':roof['guid'],
        'hostGeometryHash':C.RUN.digest(C.ROOF.geometry_signature(bodies[roof['guid'].lower()])),
        'hostMaterialBindings':roof['materialBindings'],'hostHomeStory':bodies[roof['guid'].lower()]['homeStory'],
        'expectedPlacement':{k:data[k] for k in ('floorIndex','basePoint','xAxis','yAxis','zAxis')},
        'projectMaterialSelection':selection,'sourceSectionMeters':{'width':width,'height':height},'modelDerivedLengthMeters':length,
        'modelSpanAuthority':{'start':'Actual accepted batten underside low edge','end':'Actual upper wall inner face','startY':start,'endY':end},
        'nativeDependencyBodies':[{'guid':e['guid'],'geometryHash':C.RUN.digest(C.ROOF.geometry_signature(bodies[e['guid'].lower()])),
            'materialBindings':bodies[e['guid'].lower()]['materialBindings'],'homeStory':bodies[e['guid'].lower()]['homeStory']} for e in [batten,wall]+segment_dependencies],
        'physicalContact':{'counterpartGuid':batten['guid'],'expectedAreaSquareMeters':width*facts['c4']['values']['value_2']/1000,
            'sourceRelation':'battens_supported_by_counterbattens','sourceEntityPair':['c4','c5']},
        'classification':{'role':'counterbatten','scope':'SOURCE_ROLE_IN_BIM_GRAPH; NATIVE_CLASSIFICATION_ITEM_NOT_ASSIGNED'},
        'assemblyWriteAllowed':False,'scope':'COMPLETE_BOUNDED_BATTEN_COUNTERBATTEN_SUPPORT_CONTACT; FULL_MANUFACTURER_ASSEMBLY_NOT_VERIFIED',
        'materialAcceptance':'VERIFIED_EXISTING_PROJECT_TIMBER; SOURCE_GRADE_NOT_SPECIFIED','engineeringAcceptance':'NOT_VERIFIED',
        'missingAssemblyDimensionEntities':candidate['missingDimensionEntities']}
    plan=C.bind_plan(source,[{'id':'source-support-counterbatten-c5','command':'CreateMorphs','params':{'morphsData':[data]}}],['morph'],{'sourceDetailBinding':binding})
    return {'status':'OFFLINE_SOURCE_SUPPORT_JUNCTION_PREPARED','binding':binding,'plan':plan,'nativeWrites':0}


def verify_counterbatten_contact(api,binding,created_guid):
    """Independent actual-body/contact/collision readback of the new member."""
    verify_source_section_binding(api,binding)
    native=C.G.normalize_dump(api('GetModelDumpV1',{}))
    bodies={e['guid'].lower():e for e in native['elements']}
    counterpart=binding['physicalContact']['counterpartGuid'].lower();created=created_guid.lower()
    if created not in bodies or created==counterpart:raise ValueError('COUNTERBATTEN_NEW_BODY_NOT_DISTINCT')
    contacts=C.G.shared_surfaces(bodies,{counterpart:counterpart,created:created})
    area=sum(r['sharedAreaSquareMeters'] for r in contacts if set(r['guids'])=={counterpart,created})
    if area<=0 or not C.RUN.close(area,binding['physicalContact']['expectedAreaSquareMeters'],1e-6):
        raise ValueError('COUNTERBATTEN_ACTUAL_SUPPORT_AREA_MISMATCH')
    collision=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':created}}],
        'elementsGroup2':[{'elementId':{'guid':g}} for g,e in bodies.items() if g!=created and e.get('bodies')]})
    if collision.get('collisions')!=[]:raise ValueError('COUNTERBATTEN_UNPLANNED_NATIVE_COLLISION')
    return {'status':'LIVE_SOURCE_SUPPORT_CONTACT_PASS','newGuid':created,'counterpartGuid':counterpart,
        'sourceDetailId':binding['detailId'],'sourceRelation':binding['physicalContact']['sourceRelation'],
        'sharedAreaSquareMeters':area,'sourceSectionMeters':binding['sourceSectionMeters'],
        'modelDerivedLengthMeters':binding['modelDerivedLengthMeters'],'nativeBoundsMeters':C.ROOF.bounds(bodies[created]),
        'actualMaterialBindings':bodies[created]['materialBindings'],'actualHomeStory':bodies[created]['homeStory'],
        'nativeBodyHash':C.RUN.digest(C.ROOF.geometry_signature(bodies[created])),
        'physicalContact':'PASS_GEOMETRY','nativeVolumeCollision':collision,'logicalBinding':'SOURCE_RELATION_IN_BIM_GRAPH',
        'nativeParentChildRelation':'NOT_CLAIMED_FOR_MORPH','classification':binding['classification'],
        'completeManufacturerAssembly':'NOT_VERIFIED','engineeringAcceptance':'NOT_VERIFIED'}


def resolve_existing_classification(api,selection):
    """Reuse the retained native classification tree reader; never create it."""
    from archicad_template_builder import _flatten_classification_items
    systems=api('API.GetAllClassificationSystems',{}).get('classificationSystems',[])
    found=[s for s in systems if s['name']==selection['systemName'] and s['version']==selection['systemVersion']]
    if len(found)!=1 or found[0]['classificationSystemId']['guid'].lower()!=selection['systemGuid'].lower():
        raise ValueError('JUNCTION_CLASSIFICATION_SYSTEM_INVALIDATED')
    items=api('API.GetAllClassificationsInSystem',{'classificationSystemId':found[0]['classificationSystemId']}).get('classificationItems',[])
    flat={};_flatten_classification_items(items,flat)
    if selection['itemId'] not in flat or flat[selection['itemId']]['guid'].lower()!=selection['itemGuid'].lower():
        raise ValueError('JUNCTION_CLASSIFICATION_ITEM_INVALIDATED')
    return {'status':'EXISTING_NATIVE_CLASSIFICATION_SELECTION_PASS','system':found[0],'item':flat[selection['itemId']]}


def verify_member_classification(api,guid,selection):
    resolve_existing_classification(api,selection)
    rows=api('GetClassificationsOfElements',{'elements':[{'elementId':{'guid':guid}}],
        'classificationSystemIds':[{'classificationSystemId':{'guid':selection['systemGuid']}}]}).get('elementClassifications',[])
    wanted={'classificationSystemId':{'guid':selection['systemGuid']},'classificationItemId':{'guid':selection['itemGuid']}}
    values=rows[0].get('classificationIds') if len(rows)==1 else None
    actual=values[0] if isinstance(values,list) and len(values)==1 else None
    if isinstance(actual,dict) and set(actual)=={'classificationId'}:actual=actual['classificationId']
    # Installed1.5.10 returns direct ClassificationId rows although the
    # catalog advertises a classificationId wrapper. Keep both exact shapes.
    if actual!=wanted:
        raise ValueError('JUNCTION_ACTUAL_CLASSIFICATION_READBACK_MISMATCH')
    return {'status':'ACTUAL_NATIVE_MEMBER_CLASSIFICATION_PASS','elementGuid':guid,'selection':selection,'nativeReadback':rows,
        'scope':'Native Beam classification of source counterbatten; tool remains editable Morph; load-bearing suitability not inferred'}
