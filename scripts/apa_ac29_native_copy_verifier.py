"""Existing multi-prototype copy checks attached to the shared native registry.

Only explicit horizontal MoveElements(copy=true), standalone ungrouped roots,
story zero, one complete Column/Beam segment or a closed standalone Object.
No execution, new planner, native primitive creation or geometry engine.
"""
import json
import math
import collections
import archicad_scene_run as R
import archicad_connected_components as C
import apa_ac29_multi_prototype_native_copy as M
import apa_ac29_native_group_clone_verifier as G
from apa_ac29_dynamic_write_scopes import NativeVerifier

CMD='MoveElements'
NULL='00000000-0000-0000-0000-000000000000'
need=G.require


def canonical(value):return json.loads(R.canonical(value))


def require_ungrouped(api,guids):
    guids=sorted(guids)
    for start in range(0,len(guids),50):
        part=guids[start:start+50]
        reply=api('GetNativeGroupRootsV1',dict(elements=[dict(elementId=dict(guid=g)) for g in part]))
        rows=reply.get('groups')
        need(reply.get('nativeModelWrites')==0 and isinstance(rows,list) and len(rows)==len(part),
             'MASS_COPY_NATIVE_GROUP_READBACK_REQUIRED')
        found={}
        for row in rows:
            need(isinstance(row,dict) and 'error' not in row,'MASS_COPY_UNKNOWN_NATIVE_GROUP_MEMBERSHIP')
            guid=row.get('elementId',{}).get('guid','').lower()
            need(guid in part and guid not in found and
                 row.get('groupId',{}).get('guid','').lower()==NULL and
                 row.get('rootGroupId',{}).get('guid','').lower()==NULL,
                 'MASS_COPY_EXISTING_GROUP_REQUIRES_WHOLE_GROUP_ADAPTER')
            found[guid]=True
        need(set(found)==set(part),'MASS_COPY_GROUP_ID_SET_DRIFT')


def facts(api,nodes,guids,native):
    details=M.SINGLE.column_details(api,sorted(guids));output={}
    for guid in sorted(guids):
        row=nodes[guid];kind=row['type'];detail=details[guid]
        need(kind in M.TYPES and row.get('homeStory')==detail.get('floorIndex')==0,
             'MASS_COPY_ONLY_KNOWN_STANDALONE_STORY_ZERO')
        d=detail['details'];point=d.get('begCoordinate') if kind=='Beam' else d.get('origin')
        need(isinstance(point,dict),'MASS_COPY_TYPED_NATIVE_ORIGIN_REQUIRED')
        z=d.get('zCoordinate') if kind in ('Column','Beam') else point.get('z')
        anchor=dict(x=point.get('x'),y=point.get('y'),z=z);M.vector(anchor)
        typed=M.source_detail_fingerprint(detail,kind,anchor)
        children=M.owned_children(nodes,guid,kind)
        solid=M.solid_fingerprint(row,children,anchor,parent_guid=guid)
        output[guid]=canonical(dict(type=kind,anchor=anchor,typed=typed,
            solid=G.materialized_solid(solid,native),childGuids=[g for g,_ in children]))
    return output


def semantic_digest(native,guids):
    """Existing geometry signature plus oriented face/full-material records."""
    rows=native.get('materials');need(isinstance(rows,list),'MASS_COPY_MATERIAL_POOL_REQUIRED')
    pool={r['id']:{k:v for k,v in r.items() if k not in ('id','modelMaterialIndex')} for r in rows}
    need(len(pool)==len(rows),'MASS_COPY_DUPLICATE_MATERIAL_POOL_ID')
    selected={}
    for row in native['elements']:
        guid=row['guid'].lower()
        if guid not in guids:continue
        faces=[]
        for body in row.get('bodies',[]):
            verts=[dict(zip(('x','y','z'),v)) for v in body['vertices']]
            for face in body['faces']:
                cs=face['contours'];need(face['materialId'] in pool,'MASS_COPY_UNRESOLVED_FACE_MATERIAL')
                key=C.body_face_keys(dict(vertices=verts,polygons=[dict(vertexIds=cs[0],holes=cs[1:])]))
                faces.append(dict(geometry=key,material=pool[face['materialId']],nativeStatus=face.get('nativeStatus')))
        selected[guid]=dict(geometry=C.ROOF.geometry_signature(row),materialBindings=row.get('materialBindings'),
            relationships=row.get('relationships'),faces=sorted(faces,key=R.canonical))
    need(set(selected)==set(guids),'MASS_COPY_COMPLETE_RETAINED_NATIVE_FACTS_REQUIRED')
    return R.digest(selected)


def verify_before(*,api,command,parameters,affected,native_before):
    need(command==CMD and not affected and isinstance(parameters,dict) and
         set(parameters)=={'elementsWithMoveVectors'},'MASS_COPY_ONLY_EXACT_CREATE_BATCH')
    rows=parameters['elementsWithMoveVectors']
    need(isinstance(rows,list) and 1<=len(rows)<=200,'MASS_COPY_BOUNDED_NATIVE_BATCH')
    shifts={}
    for row in rows:
        need(isinstance(row,dict) and set(row)=={'elementId','moveVector','copy'} and row['copy'] is True,
             'MASS_COPY_RELOCATION_OR_MIXED_BATCH_REJECTED')
        need(isinstance(row['elementId'],dict) and set(row['elementId'])=={'guid'},'MASS_COPY_EXACT_SOURCE_ID')
        guid=row['elementId']['guid'].lower();need(G.GROUP_GUID.fullmatch(guid),'MASS_COPY_SOURCE_GUID_REQUIRED')
        vector=row['moveVector'];need(isinstance(vector,dict) and set(vector)=={'x','y','z'} and
            all(type(v) in (int,float) and math.isfinite(v) and abs(v)<=10000 for v in vector.values()) and
            vector['z']==0 and (vector['x']!=0 or vector['y']!=0),'MASS_COPY_EXPLICIT_HORIZONTAL_NONZERO_VECTOR')
        shifts.setdefault(guid,[]).append(vector)
    need(len(shifts)<=16 and all(len({R.canonical(v) for v in vs})==len(vs) for vs in shifts.values()),
         'MASS_COPY_UNIQUE_BOUNDED_PROTOTYPES_AND_TARGETS')
    nodes={r['guid'].lower():r for r in native_before['elements']}
    need(len(nodes)==len(native_before['elements']) and set(shifts)<=set(nodes),'MASS_COPY_SOURCE_NOT_IN_NATIVE_MODEL')
    require_ungrouped(api,shifts)
    source=facts(api,nodes,shifts,native_before);prototypes=[];elements={};targets={}
    for guid,values in shifts.items():
        anchor=source[guid]['anchor'];targets[guid]=[{k:anchor[k]+v[k] for k in ('x','y','z')} for v in values]
        prototypes.append(dict(prototypeGuid=guid,prototypeType=source[guid]['type'],sourceAnchor=anchor,targets=targets[guid]))
        elements[guid]=(nodes[guid],M.owned_children(nodes,guid,source[guid]['type']))
    collision=M.verify_batch_layout(prototypes,elements,nodes,targets)
    return canonical(dict(status='MASS_COPY_TYPED_UNGROUPED_NATIVE_SOURCE_LAYOUT_PASS',
        paramsSHA256=R.digest(parameters),baselineGuids=sorted(nodes),
        retainedSemanticSHA256=semantic_digest(native_before,set(nodes)),sourceFacts=source,
        prototypes=prototypes,collisionProof=collision,copyCount=len(rows)))


def verify_after(*,api,command,parameters,native_response,before_guids,after_guids,affected,
                 native_before,native_after,source_proof):
    need(command==CMD and not affected and source_proof.get('status')=='MASS_COPY_TYPED_UNGROUPED_NATIVE_SOURCE_LAYOUT_PASS'
         and source_proof['paramsSHA256']==R.digest(parameters) and set(source_proof['baselineGuids'])==set(before_guids),
         'MASS_COPY_POST_SOURCE_OR_PARAMETERS_DRIFT')
    replies=native_response.get('executionResults') if isinstance(native_response,dict) else None
    need(isinstance(replies,list) and len(replies)==source_proof['copyCount'] and
         all(isinstance(r,dict) and r.get('success') is True for r in replies),'MASS_COPY_NATIVE_RESPONSE_UNKNOWN_NO_REPLAY')
    nodes={r['guid'].lower():r for r in native_after['elements']};old=set(before_guids);new=set(after_guids)-old
    task=dict(prototypes=source_proof['prototypes']);counts=M.expected_new_types(task)
    need(set(nodes)==set(after_guids) and old<=set(nodes) and len(new)==sum(counts.values()) and
         dict(collections.Counter(nodes[g]['type'] for g in new))==counts,'MASS_COPY_EXACT_ROOT_AND_SEGMENT_GUID_DELTA')
    need(semantic_digest(native_after,old)==source_proof['retainedSemanticSHA256'],'MASS_COPY_ORIGINAL_NATIVE_GEOMETRY_OR_MATERIAL_CHANGED')
    source=source_proof['sourceFacts'];require_ungrouped(api,source)
    current_source=facts(api,nodes,source,native_after)
    need(G.same_native_fact(current_source,source),'MASS_COPY_ORIGINAL_TYPED_SOURCE_CHANGED')
    roots={g for g in new if nodes[g]['type'] in M.TYPES};require_ungrouped(api,roots)
    copied=facts(api,nodes,roots,native_after);seen=set();children=set();mapping=[]
    for group in source_proof['prototypes']:
        guid=group['prototypeGuid'];fact=source[guid]
        for target in group['targets']:
            candidates=[g for g,v in copied.items() if v['type']==fact['type'] and
                all(M.SINGLE.almost(v['anchor'][k],target[k]) for k in ('x','y','z')) and
                G.same_native_fact(v['typed'],fact['typed']) and G.same_native_fact(v['solid'],fact['solid'])]
            need(len(candidates)==1 and candidates[0] not in seen,'MASS_COPY_NATIVE_POSITION_BREP_ATTRIBUTES_NOT_UNIQUE')
            g=candidates[0];owned=set(copied[g]['childGuids'])
            need(owned<=new and not owned.intersection(children),'MASS_COPY_NEW_CHILD_GUID_OWNERSHIP_DRIFT')
            seen.add(g);children|=owned;mapping.append(dict(sourceGuid=guid,newRootGuid=g,newChildGuids=sorted(owned),target=target))
    need(seen==roots and seen|children==new,'MASS_COPY_ALL_NEW_GUIDS_MUST_BE_ACCOUNTED')
    return dict(status='MASS_COPY_SHARED_REGISTRY_NATIVE_GUID_BREP_READBACK_PASS',
        newPhysicalCopyCount=source_proof['copyCount'],newRootGuids=sorted(seen),newChildGuids=sorted(children),
        unchangedPrototypeGuids=sorted(source),finalGuidCount=len(nodes),mapping=mapping,
        allOriginalGeometryAndFaceMaterialsPreserved=True,allSelectedSourcesUngrouped=True)


def installed_copy_verifiers():
    return {'VerifiedNativeBatchCopy':NativeVerifier(verifier_id='VerifiedNativeBatchCopy',
        command=CMD,effect='CREATE',before=verify_before,after=verify_after)}
