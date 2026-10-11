"""Native geometry verification attached to the existing authored readback.

Retains the original dump normalizer/topology verifier. NetworkX relates owned
GUIDs; Shapely is a 2D candidate tool. Exact collision results come from Tapir.
"""
import copy
import hashlib
import importlib.util
import math
from pathlib import Path
import archicad_project_accelerator as A
import archicad_accelerator_integration as I


def normalize_dump(raw):
    spec=importlib.util.spec_from_file_location('retained_native_dump',I.ROOT/'archicad-addon/Examples/model_dump_v1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.normalize(copy.deepcopy(raw))


def shared_surfaces(elements, owners):
    """Compare actual coplanar BREP face contours, preserving polygon holes.

    Surface contact is distinct from native body intersection and load transfer.
    No new solid/boolean engine or model modification is introduced.
    """
    from shapely.geometry import Polygon
    planes={};areas={}
    for native_guid,parent in owners.items():
        for body in elements[native_guid]['bodies']:
            vertices=body['vertices']
            for face in body['faces']:
                contours=face['contours'];outer=[vertices[i] for i in contours[0]]
                origin=outer[0];normal=None
                for i in range(1,len(outer)-1):
                    a=[outer[i][k]-origin[k] for k in range(3)]
                    b=[outer[i+1][k]-origin[k] for k in range(3)]
                    cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
                    length=math.sqrt(sum(v*v for v in cross))
                    if length>1e-12:normal=[v/length for v in cross];break
                if normal is None:continue  # Zero-area contour cannot prove contact.
                first=next(v for v in normal if abs(v)>1e-8)
                if first<0:normal=[-v for v in normal]
                distance=sum(normal[k]*origin[k] for k in range(3))
                points=[vertices[i] for c in contours for i in c]
                if any(abs(sum(normal[k]*v[k] for k in range(3))-distance)>1e-6 for v in points):
                    raise ValueError('NONPLANAR_NATIVE_FACE_CONTACT_NOT_SUPPORTED')
                drop=max(range(3),key=lambda k:abs(normal[k]));axes=[k for k in range(3) if k!=drop]
                polygon=Polygon([[v[k] for k in axes] for v in outer],
                    [[[vertices[i][k] for k in axes] for i in c] for c in contours[1:]])
                if not polygon.is_valid:raise ValueError('INVALID_NATIVE_FACE_POLYGON')
                key=tuple(round(v,6) for v in normal)+(round(distance,6),)
                for other,previous in planes.get(key,[]):
                    if other==parent:continue
                    area=polygon.intersection(previous).area/abs(normal[drop])
                    if area>1e-8:
                        pair=tuple(sorted((parent,other)));areas[pair]=areas.get(pair,0)+area
                planes.setdefault(key,[]).append((parent,polygon))
    return [{'guids':list(pair),'sharedAreaSquareMeters':area,
             'evidence':'resultant-native-BREP-coplanar-surface'} for pair,area in sorted(areas.items())]


def analyze(normalized, plan, created, children, volume_pairs, surface_pairs):
    import networkx as nx
    from shapely.geometry import box, LineString, Polygon
    if normalized.get('coordinateSystem')!='ABSOLUTE_PROJECT_XYZ' or normalized.get('units')!='m':
        raise ValueError('GEOMETRY_COORDINATES_NOT_ABSOLUTE_METERS')
    elements={e['guid'].lower():e for e in normalized['elements']}
    operations={s['id']:s for s in plan['graph']['operations']}
    owners={v['guid'].lower():v['guid'].lower() for v in created.values()}
    for parent, guids in children.items():
        for guid in guids:
            row=elements.get(guid)
            if not row or row['type']!='ColumnSegment' or row.get('relationships',{}).get('hostGuid','').lower()!=parent:
                raise ValueError('DUMP_COLUMN_SEGMENT_OWNER_MISMATCH')
            owners[guid]=parent
    bounds={};graph=nx.Graph()
    for sid,value in created.items():
        guid=value['guid'].lower();row=elements.get(guid)
        if row is None or row['type']!=value['kind'] or row['homeStory']!=value['floorIndex']:
            raise ValueError('DUMP_PRIMARY_GUID_TYPE_STORY_MISMATCH')
        members=[row]+[elements[g] for g in children.get(guid,[])]
        points=[v for member in members for body in member['bodies'] for v in body['vertices']]
        if not points:raise ValueError('PRIMARY_NATIVE_GEOMETRY_MISSING: '+sid)
        bounds[guid]={'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
        graph.add_node(guid,kind=row['type'],step=sid)
        step=operations[sid];data=next(iter(step['params'].values()))[0]
        floor=A.RUN.story_level_for_floor(plan['storyBindings'],value['floorIndex'])
        if row['type']=='Wall':
            bottom=floor+data['zCoordinate'];top=bottom+data['height']
            allowed=LineString([(data[k]['x'],data[k]['y']) for k in ('begCoordinate','endCoordinate')]).buffer(data['thickness']/2,cap_style=3).buffer(1e-6)
        elif row['type']=='Slab':
            top=data['level'];bottom=top-data['thickness']
            allowed=Polygon([(v['x'],v['y']) for v in data['polygonCoordinates']]).buffer(1e-6)
        elif row['type']=='Column':
            bottom=data['coordinates']['z'];top=bottom+data['height']
            x,y=data['coordinates']['x'],data['coordinates']['y']
            allowed=box(x-data['width']/2,y-data['depth']/2,x+data['width']/2,y+data['depth']/2).buffer(1e-6)
        else:
            host=data['ownerWallId']['guid']['$createdGuid'];parent=created[host]['guid'].lower()
            if row.get('relationships',{}).get('hostGuid','').lower()!=parent:
                raise ValueError('DUMP_OPENING_HOST_MISMATCH')
            graph.add_edge(guid,parent,evidence='native-host')
            # GDL frame extents differ from nominal opening dimensions; typed
            # opening dimensions are verified by the original SceneWriter.
            continue
        actual=bounds[guid]
        if not A.RUN.close(actual['min'][2],bottom,1e-6) or not A.RUN.close(actual['max'][2],top,1e-6):
            raise ValueError('NATIVE_BODY_Z_EXTENT_MISMATCH: '+sid)
        material=data.get('buildingMaterialId',{'guid':plan['slabBasicMaterialGuid']})['guid'].lower()
        for member in members:
            if member['bodies'] and member.get('materialBindings',{}).get('buildingMaterial',{}).get('guid','').lower()!=material:
                raise ValueError('NATIVE_BODY_MATERIAL_GUID_MISMATCH: '+sid)
        from shapely.geometry import Point
        if any(not allowed.covers(Point(v[0],v[1])) for v in points):
            raise ValueError('NATIVE_BODY_OUTSIDE_DECLARED_XY: '+sid)
    def pairs(rows):
        found=set()
        for r in rows:
            left=r['elementId1']['guid'].lower();right=r['elementId2']['guid'].lower()
            if left not in owners or right not in owners:raise ValueError('COLLISION_CONTAINS_UNOWNED_GUID')
            if type(r.get('hasBodyCollision')) is not bool or type(r.get('hasClearenceCollision')) is not bool:
                raise ValueError('INVALID_NATIVE_COLLISION_FLAGS')
            if r['hasBodyCollision'] and owners[left]!=owners[right]:found.add(tuple(sorted((owners[left],owners[right]))))
        return found
    volume=pairs(volume_pairs);surface=pairs(surface_pairs)
    for left,right in volume|surface:
        graph.add_edge(left,right,evidence='native-volume-intersection' if (left,right) in volume else 'native-surface-check')
    contacts=shared_surfaces(elements,owners)
    for contact in contacts:
        graph.add_edge(*contact['guids'],evidence=contact['evidence'])
    xy_only=[];aabb_candidates=[]
    keys=sorted(bounds)
    for i,left in enumerate(keys):
        for right in keys[i+1:]:
            a,b=bounds[left],bounds[right]
            pa=box(a['min'][0],a['min'][1],a['max'][0],a['max'][1])
            pb=box(b['min'][0],b['min'][1],b['max'][0],b['max'][1])
            if not pa.intersects(pb):continue
            z_overlap=min(a['max'][2],b['max'][2])-max(a['min'][2],b['min'][2])
            pair=[left,right]
            if z_overlap<=1e-6 and (left,right) not in volume:xy_only.append(pair)
            else:aabb_candidates.append(pair)
    return {'status':'NATIVE_AUTHORED_GEOMETRY_READBACK_PASS','primaryCoverage':len(bounds),
        'columnGeometrySource':'DIRECTLY_OWNED_NATIVE_COLUMN_SEGMENTS',
        'bounds':bounds,'nativeVolumeIntersectionPairs':[list(p) for p in sorted(volume)],
        'nativeSurfaceCheckPairs':[list(p) for p in sorted(surface-volume)],
        'xyOverlapWithoutNativeVolumeCollision':xy_only,'aabbCandidates':aabb_candidates,
        'relationshipComponents':[sorted(c) for c in nx.connected_components(graph)],
        'graphEdges':[{'guids':[a,b],**v} for a,b,v in graph.edges(data=True)],
        'sharedNativeSurfaces':contacts,
        'collisionEngine':'Tapir.GetCollisions; Shapely/AABB produce candidates only',
        'structuralAcceptance':'NOT_VERIFIED','jointQualityAcceptance':'NOT_VERIFIED'}


def run(api, plan, created, inventory, folder):
    from archicad_authored_extension import verify_model
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if A.RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding'] or A.inventory_guids(api)!=inventory:
        raise ValueError('GEOMETRY_TARGET_OR_INVENTORY_DRIFT')
    verified=verify_model(api,plan,created);children=A.column_subelements(api,verified)
    raw=api('GetModelDumpV1',{});A.write_json(folder/'native-model.json',raw)
    topology=I.verify_saved_dump(folder/'native-model.json')
    normalized=normalize_dump(raw);A.write_json(folder/'normalized-model.json',normalized)
    group=[{'elementId':{'guid':v['guid']}} for v in verified.values()]
    results=[]
    for surface in (False,True):
        rows=[]
        # Disjoint groups: each unordered primary pair is tested exactly once.
        for i in range(len(group)-1):
            response=api('GetCollisions',{'elementsGroup1':[group[i]],'elementsGroup2':group[i+1:],
                'settings':{'volumeTolerance':1e-8,'performSurfaceCheck':surface,'surfaceTolerance':1e-8}})
            if not isinstance(response.get('collisions'),list):raise ValueError('NATIVE_COLLISION_RESULT_MISSING')
            rows.extend(response['collisions'])
        results.append(rows)
    report=analyze(normalized,plan,verified,children,*results)
    if A.RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding'] or A.inventory_guids(api)!=inventory:
        raise ValueError('GEOMETRY_AFTER_READ_DRIFT')
    report.update(topologyCounts=topology['counts'],geometryScope=normalized['geometryScope'],modelWriteAttempts=0,inventoryUnchanged=True,
        dumpSha256={name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
                    for name in ('native-model.json','normalized-model.json')})
    A.write_json(folder/'geometry.json',report)
    return report
