"""Local IFC coordination/export over the shared native context.

Exports stay local. Aggregate route IDs may differ from the exported physical
duct's IFC root: missing mappings are reported rather than silently matched.
"""
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import math
from collections import Counter
import archicad_connected_components as C


def inspect_export(path,context,mapping):
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.unit
    model=ifcopenshell.open(str(path))
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    rows=[]
    for sid,native in context['elements'].items():
        identifier=mapping[native['guid'].lower()]
        try:element=model.by_guid(identifier)
        except RuntimeError:element=None
        row={'stepId':sid,'nativeKind':native['kind'],'ifcId':identifier,'status':'IFC_ROOT_NOT_EXPORTED'}
        physical=False
        exported=[element] if element else []
        if element is None and native.get('physicalIfcIds'):
            try:exported=[model.by_guid(identifier) for identifier in native['physicalIfcIds']]
            except RuntimeError:exported=[]
            if exported:
                element=exported[0];physical=True
                row.update(aggregateIfcIdNotExported=identifier,physicalIfcIds=native['physicalIfcIds'],
                    physicalNativeGuids=native['physicalElementGuids'],mappingScope='ACTUAL_EXPORTED_PHYSICAL_DUCT_MEMBERS; CONTAINER_IS_NOT_AN_IFC_ROOT')
        if element is None and native.get('physicalIfcId'):
            try:element=model.by_guid(native['physicalIfcId'])
            except RuntimeError:element=None
            if element:
                physical=True
                exported=[element]
                row.update(aggregateIfcIdNotExported=identifier,physicalIfcId=native['physicalIfcId'],
                    physicalNativeGuid=native['physicalElementGuid'],mappingScope='EXPORTED_PHYSICAL_DUCT; CONTAINER_IS_NOT_AN_IFC_ROOT')
        if element:
            row.update(ifcType=element.is_a(),status='IFC_IDENTITY_MAPPED')
            try:
                points=[]
                for member in exported:
                    shape=ifcopenshell.geom.create_shape(settings,member);v=shape.geometry.verts
                    points.extend(v[i:i+3] for i in range(0,len(v),3))
                if not points:raise ValueError('EMPTY_IFC_SHAPE')
                bounds=[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(3)]
                source_bounds=native.get('physicalBounds',native['bounds']) if physical else native['bounds']
                native_bounds=[(min(b[i][0] for b in source_bounds),max(b[i][1] for b in source_bounds)) for i in range(3)]
                delta=max(abs(a-b) for left,right in zip(bounds,native_bounds) for a,b in zip(left,right))
                row.update(ifcBoundsMeters=bounds,nativeBoundsMeters=native_bounds,boundsDeltaMeters=delta,
                    status=('IFC_PHYSICAL_ROUTE_WORLD_BOUNDS_MATCH' if physical else 'IFC_NATIVE_WORLD_BOUNDS_MATCH') if delta<1e-5 else 'IFC_NATIVE_BOUNDS_MISMATCH')
                if native['kind']=='Opening' and native.get('geometryAuthority')=='TWO_ACTUAL_NATIVE_HOST_INNER_FACE_CONTOURS':
                    host=[e for e in context['elements'].values() if e['guid'].lower()==native.get('hostGuid','').lower()]
                    if len(host)!=1:raise ValueError('IFC_OPENING_HOST_NOT_UNIQUE')
                    host_ifc=mapping[host[0]['guid'].lower()]
                    if not any(r.RelatedOpeningElement.GlobalId==identifier and r.RelatingBuildingElement.GlobalId==host_ifc for r in model.by_type('IfcRelVoidsElement')):
                        raise ValueError('IFC_OPENING_HOST_RELATION_MISMATCH')
                    h=[(min(b[i][0] for b in host[0]['bounds']),max(b[i][1] for b in host[0]['bounds'])) for i in range(3)]
                    clipped=[(max(a[0],b[0]),min(a[1],b[1])) for a,b in zip(bounds,h)]
                    cut_delta=max(abs(a-b) for left,right in zip(clipped,native_bounds) for a,b in zip(left,right))
                    row.update(ifcHostCutBoundsMeters=clipped,hostCutDeltaMeters=cut_delta,
                        geometryScope='IFC_CUTTER_INTERSECTION_WITH_VERIFIED_HOST_BOUNDS; STANDALONE_CUTTER_EXTENTS_REMAIN_RECORDED',
                        status='IFC_OPENING_HOST_CUT_BOUNDS_MATCH' if cut_delta<1e-5 else 'IFC_OPENING_HOST_CUT_BOUNDS_MISMATCH')
            except Exception as exc:row.update(status='IFC_IDENTITY_ONLY_GEOMETRY_NOT_VERIFIED',reason=type(exc).__name__+': '+str(exc))
        rows.append(row)
    return {'schema':model.schema,'ifcLengthUnitScaleToMeters':scale,'ifcopenshellVersion':ifcopenshell.version,
        'elements':rows,'mappedCount':sum(r['status']!='IFC_ROOT_NOT_EXPORTED' for r in rows),
        'boundsMatchCount':sum(r['status'] in {'IFC_NATIVE_WORLD_BOUNDS_MATCH','IFC_PHYSICAL_ROUTE_WORLD_BOUNDS_MATCH','IFC_OPENING_HOST_CUT_BOUNDS_MATCH'} for r in rows),
        'openingHostCutMappings':sum(r['status']=='IFC_OPENING_HOST_CUT_BOUNDS_MATCH' for r in rows),
        'physicalRouteMappings':sum(r['status']=='IFC_PHYSICAL_ROUTE_WORLD_BOUNDS_MATCH' for r in rows),
        'requestedCount':len(rows),'status':'IFC_COORDINATION_BOUNDS_PASS_WITH_EXPLICIT_PHYSICAL_ROUTE_MAPPING' if all(r['status'] in {'IFC_NATIVE_WORLD_BOUNDS_MATCH','IFC_PHYSICAL_ROUTE_WORLD_BOUNDS_MATCH','IFC_OPENING_HOST_CUT_BOUNDS_MATCH'} for r in rows) else 'IFC_COORDINATION_WITH_EXPLICIT_GAPS',
        'scope':'GUID + world bounds; Opening uses native host hole and IFC host-cut intersection; not full face/quantity/engineering equivalence',
        'structuralAcceptance':'NOT_VERIFIED'}


def inspect_exchange_semantics(path):
    """Observe real IFC relationships separately from coordinate agreement.

    Structural data are exported only when present in the actual file; an
    architectural body is never silently converted into an analytical member.
    """
    import ifcopenshell
    import ifcopenshell.util.element
    model=ifcopenshell.open(str(path))
    openings=[{'openingIfcId':r.RelatedOpeningElement.GlobalId,'hostIfcId':r.RelatingBuildingElement.GlobalId,
        'hostIfcType':r.RelatingBuildingElement.is_a()} for r in model.by_type('IfcRelVoidsElement')]
    connections=[{'firstPortIfcId':r.RelatingPort.GlobalId,'secondPortIfcId':r.RelatedPort.GlobalId}
        for r in model.by_type('IfcRelConnectsPorts')]
    materials=[]
    for e in model.by_type('IfcElement'):
        material=ifcopenshell.util.element.get_material(e)
        if material:materials.append({'ifcId':e.GlobalId,'materialType':material.is_a(),
            'materialName':getattr(material,'Name',None)})
    analytical=[]
    for e in model.by_type('IfcStructuralMember'):
        analytical.append({'ifcId':e.GlobalId,'ifcType':e.is_a(),'name':e.Name,
            'representationPresent':e.Representation is not None})
    return {'schema':model.schema,'voidRelations':openings,'nativePortRelationsExported':connections,
        'materialAssignments':materials,'analyticalMembers':analytical,
        'analysisModels':[{'ifcId':e.GlobalId,'name':e.Name} for e in model.by_type('IfcStructuralAnalysisModel')],
        'loadGroupCount':len(model.by_type('IfcStructuralLoadGroup')),
        'analyticalExchangeStatus':'ACTUAL_IFC_ANALYTICAL_DATA_PRESENT_REQUIRES_ENGINEER_REVIEW' if analytical else 'NO_ANALYTICAL_MEMBERS_IN_ACTUAL_EXPORT',
        'safStatus':'EXTERNAL_DEPENDENCY_NATIVE_SAF_FILE_AND_QUALIFIED_MAPPING_REQUIRED',
        'semanticCompatibility':'NOT_VERIFIED','calculationResults':'NOT_PROVIDED'}


def native_body_quantities(element):
    """Planar resultant BREP quantities, with closure and orientation evidence.

    Curved bodies and nonplanar faces are reported rather than approximated.
    Face holes use Shapely's actual inner contours, independent of ring winding.
    """
    from shapely.geometry import Polygon
    area=volume=0.;bodies=element.get('bodies',[])
    if not bodies:return {'status':'NATIVE_BODY_NOT_AVAILABLE'}
    try:
        for body in bodies:
            if body.get('curved'):raise ValueError('CURVED_NATIVE_BODY_NOT_QUANTIFIED')
            vertices=body['vertices'];edges=Counter();signed_volume=0.;area_vector=[0.,0.,0.];body_area=0.
            if not body.get('closed'):raise ValueError('NATIVE_BODY_NOT_CLOSED')
            for face in body['faces']:
                rings=face['contours'];points=[vertices[i] for i in rings[0]]
                n=[sum(p[(k+1)%3]*q[(k+2)%3]-p[(k+2)%3]*q[(k+1)%3] for p,q in zip(points,points[1:]+points[:1])) for k in range(3)]
                length=math.sqrt(sum(x*x for x in n))
                if length<1e-12:raise ValueError('NATIVE_FACE_DEGENERATE')
                n=[x/length for x in n];drop=max(range(3),key=lambda k:abs(n[k]));axes=[k for k in range(3) if k!=drop]
                if any(abs(sum(n[k]*(vertices[i][k]-points[0][k]) for k in range(3)))>1e-6 for ring in rings for i in ring):
                    raise ValueError('NATIVE_FACE_NONPLANAR')
                project=lambda ring:[tuple(vertices[i][k] for k in axes) for i in ring]
                polygon=Polygon(project(rings[0]),[project(r) for r in rings[1:]])
                if not polygon.is_valid or polygon.area<=0:raise ValueError('NATIVE_FACE_CONTOURS_INVALID')
                face_area=polygon.area/abs(n[drop]);area+=face_area;body_area+=face_area
                for k in range(3):area_vector[k]+=face_area*n[k]
                centroid=[0.,0.,0.];centroid[axes[0]]=polygon.centroid.x;centroid[axes[1]]=polygon.centroid.y
                centroid[drop]=(sum(n[k]*points[0][k] for k in range(3))-sum(n[k]*centroid[k] for k in axes))/n[drop]
                signed_volume+=face_area*sum(n[k]*centroid[k] for k in range(3))/3
                for ring in rings:
                    for a,b in zip(ring,ring[1:]+ring[:1]):edges[tuple(sorted((a,b)))]+=1
            if not edges or any(count!=2 for count in edges.values()):raise ValueError('NATIVE_EDGE_CLOSURE_NOT_PROVEN')
            if math.sqrt(sum(x*x for x in area_vector))>max(1e-7,body_area*1e-7):raise ValueError('NATIVE_FACE_ORIENTATION_NOT_BALANCED')
            if abs(signed_volume)<=1e-12:raise ValueError('NATIVE_VOLUME_ZERO_OR_WINDING_AMBIGUOUS')
            volume+=abs(signed_volume)
    except (ValueError,KeyError,TypeError) as exc:return {'status':'NATIVE_QUANTITIES_NOT_VERIFIED','reason':str(exc)}
    return {'status':'NATIVE_PLANAR_BREP_QUANTITIES','surfaceAreaSquareMeters':area,'volumeCubicMeters':volume,
            'bodyCount':len(bodies),'authority':'Actual resultant planar faces with holes and independently counted closed edges'}


def native_element_quantities(elements,guid):
    """Use actual SDK-owned segment bodies for a body-less Beam/Column root."""
    parent=elements.get(guid,{})
    if parent.get('bodies') or parent.get('type') not in ('Beam','Column'):
        return native_body_quantities(parent)
    children=[e for e in elements.values() if e.get('relationships',{}).get('hostGuid','').lower()==guid]
    if (not children or any(e.get('type')!=parent['type']+'Segment' or
            e.get('homeStory')!=parent.get('homeStory') or not e.get('bodies') for e in children)):
        return {'status':'NATIVE_QUANTITIES_NOT_VERIFIED','reason':'NATIVE_ASSEMBLY_SEGMENT_OWNERSHIP_NOT_PROVEN'}
    proof=native_body_quantities({'bodies':[b for e in children for b in e['bodies']]})
    proof.update(sourceSegmentGuids=sorted(e['guid'].lower() for e in children),ownershipAuthority='SDK_HOST_GUID_AND_NATIVE_SEGMENT_TYPE')
    return proof


def inspect_quantified_exchange(path,native=None,native_ifc_map=None):
    """Read actual IFC quantities/material layers/classifications and topology.

    Source qsets remain distinct from geometric measurements. Missing semantics
    are explicit; extracting an actual relationship does not certify a receiver.
    """
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element as E
    import ifcopenshell.util.shape as S
    import ifcopenshell.util.unit as U
    if native is not None and (native.get('units')!='m' or native.get('coordinateSystem')!='ABSOLUTE_PROJECT_XYZ'):
        raise ValueError('IFC_QUANTITIES_REQUIRE_NATIVE_WORLD_METRES')
    model=ifcopenshell.open(str(path));scale=U.calculate_unit_scale(model)
    settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    mapped={identifier:guid.lower() for guid,identifier in (native_ifc_map or {}).items()}
    if len(mapped)!=len(native_ifc_map or {}):raise ValueError('IFC_QUANTITY_MAP_NOT_UNIQUE')
    bodies={e['guid'].lower():e for e in (native or {}).get('elements',[])}
    rows=[]
    for e in model.by_type('IfcElement'):
        row={'ifcId':e.GlobalId,'ifcType':e.is_a(),'name':e.Name,'predefinedType':E.get_predefined_type(e),
             'sourceQuantities':E.get_psets(e,qtos_only=True),'classifications':[],'materials':[]}
        for rel in getattr(e,'HasAssociations',()):
            if rel.is_a('IfcRelAssociatesClassification'):
                c=rel.RelatingClassification;source=getattr(c,'ReferencedSource',None)
                row['classifications'].append({'type':c.is_a(),'identifier':getattr(c,'Identification',getattr(c,'ItemReference',None)),
                    'name':getattr(c,'Name',None),'source':getattr(source,'Name',None)})
        for material in E.get_materials(e):row['materials'].append({'name':material.Name,'category':getattr(material,'Category',None)})
        assignment=E.get_material(e,should_skip_usage=True)
        if assignment and assignment.is_a('IfcMaterialLayerSet'):
            row['materialLayers']=[{'name':layer.Material.Name if layer.Material else None,
                'thicknessMeters':layer.LayerThickness*scale} for layer in assignment.MaterialLayers]
        guid=mapped.get(e.GlobalId)
        if guid:
            row['nativeGuid']=guid;row['nativeQuantities']=native_element_quantities(bodies,guid)
        try:
            shape=ifcopenshell.geom.create_shape(settings,e);geometry=shape.geometry
            vertices=geometry.verts;faces=geometry.faces;edges=Counter()
            key=lambda index:tuple(round(vertices[3*index+k],8) for k in range(3))
            for i in range(0,len(faces),3):
                tri=faces[i:i+3]
                for a,b in zip(tri,tri[1:]+tri[:1]):edges[tuple(sorted((key(a),key(b))))]+=1
            closed=bool(edges) and all(count==2 for count in edges.values())
            row['geometry']={'status':'ACTUAL_IFC_TRIANGULATED_GEOMETRY','surfaceAreaSquareMeters':S.get_area(geometry),
                'closedEdgeIncidence':closed,'triangleCount':len(faces)//3,
                'dimensionsMeters':[S.get_x(geometry),S.get_y(geometry),S.get_z(geometry)]}
            if closed:row['geometry']['volumeCubicMeters']=S.get_volume(geometry)
            else:row['geometry']['volumeStatus']='IFC_MESH_CLOSURE_NOT_PROVEN'
            if guid and row['nativeQuantities']['status']=='NATIVE_PLANAR_BREP_QUANTITIES' and closed:
                nq=row['nativeQuantities'];iq=row['geometry']
                area_delta=abs(nq['surfaceAreaSquareMeters']-iq['surfaceAreaSquareMeters'])
                volume_delta=abs(nq['volumeCubicMeters']-iq['volumeCubicMeters'])
                row['nativeComparison']={'areaDeltaSquareMeters':area_delta,'volumeDeltaCubicMeters':volume_delta,
                    'status':'IFC_NATIVE_QUANTITIES_MATCH' if area_delta<=max(1e-5,nq['surfaceAreaSquareMeters']*1e-6) and volume_delta<=max(1e-7,nq['volumeCubicMeters']*1e-6) else 'IFC_NATIVE_QUANTITY_MISMATCH'}
        except Exception as exc:row['geometry']={'status':'IFC_GEOMETRY_NOT_VERIFIED','reason':type(exc).__name__+': '+str(exc)}
        rows.append(row)
    ports={}
    for r in model.by_type('IfcRelConnectsPortToElement'):ports[r.RelatingPort.GlobalId]=r.RelatedElement.GlobalId
    for r in model.by_type('IfcRelNests'):
        for p in r.RelatedObjects:
            if p.is_a('IfcDistributionPort'):ports[p.GlobalId]=r.RelatingObject.GlobalId
    connections=[{'firstPortIfcId':r.RelatingPort.GlobalId,'secondPortIfcId':r.RelatedPort.GlobalId,
        'firstOwnerIfcId':ports.get(r.RelatingPort.GlobalId),'secondOwnerIfcId':ports.get(r.RelatedPort.GlobalId)} for r in model.by_type('IfcRelConnectsPorts')]
    return {'schema':'APA_QUANTIFIED_IFC_EXCHANGE_V1','ifcSchema':model.schema,'fileSha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'lengthUnitScaleToMeters':scale,'elements':rows,'portOwnership':ports,'portConnections':connections,
        'elementConnections':[{'firstIfcId':r.RelatingElement.GlobalId,'secondIfcId':r.RelatedElement.GlobalId,'relationType':r.is_a()}
                              for r in model.by_type('IfcRelConnectsElements')],
        'openingHosts':[{'openingIfcId':r.RelatedOpeningElement.GlobalId,'hostIfcId':r.RelatingBuildingElement.GlobalId} for r in model.by_type('IfcRelVoidsElement')],
        'quantityMatchCount':sum(r.get('nativeComparison',{}).get('status')=='IFC_NATIVE_QUANTITIES_MATCH' for r in rows),
        'quantityMismatchCount':sum(r.get('nativeComparison',{}).get('status')=='IFC_NATIVE_QUANTITY_MISMATCH' for r in rows),
        'semanticCompatibility':'NOT_VERIFIED','engineeringAcceptance':'NOT_VERIFIED','nativeWrites':0}


def export_once(api,context,mapping,path,translator,journal,operation_id):
    path=Path(path).resolve()
    if path.suffix.lower()!='.ifc' or path.exists() or not path.parent.is_dir():
        raise ValueError('IFC_EXPORT_REQUIRES_NEW_LOCAL_FILE')
    if C.RUN.guarded_project(api,context['storyBindings'][0])!=context['binding'] or C.A.inventory_guids(api)!=context['inventory']:
        raise ValueError('IFC_EXPORT_NATIVE_CONTEXT_DRIFT')
    names=[r['name'] for r in api('GetIFCExportTranslators',{}).get('translators',[])]
    if names.count(translator)!=1:
        raise ValueError('IFC_TRANSLATOR_NOT_UNIQUE')
    parameters={'method':'save','ifcFilePath':str(path),'fileType':'ifc','translatorName':translator,'elementsToExport':'EntireProject'}
    intent={'operationId':operation_id,'parameters':parameters,'target':context['binding'],
        'inventoryHash':C.RUN.digest(context['inventory']),'ifcMapHash':C.RUN.digest(mapping)}
    result={'status':'BLOCKED','automaticRetry':False,'operationHash':C.RUN.digest(intent),'modelWriteAttempts':0}
    with closing(sqlite3.connect(journal)) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS isolated_ifc_exports(operation_id TEXT PRIMARY KEY,state TEXT,intent TEXT,result TEXT)');db.commit()
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO isolated_ifc_exports VALUES(?,?,?,?)',(operation_id,'ATTEMPTED',C.RUN.canonical(intent),'{}'));db.commit()
        try:
            reply=api('IFCFileOperation',parameters)
            if reply.get('success') is not True or not path.is_file():
                raise ValueError('IFC_SAVE_NOT_CONFIRMED')
            if C.RUN.guarded_project(api,context['storyBindings'][0])!=context['binding'] or C.A.inventory_guids(api)!=context['inventory']:
                raise ValueError('IFC_EXPORT_AFTER_NATIVE_CONTEXT_DRIFT')
            result.update(status='LOCAL_IFC_EXPORTED_AND_PARSED',fileSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                fileBytes=path.stat().st_size,coordination=inspect_export(path,context,mapping))
        except Exception as exc:
            result.update(status='PARTIAL_OR_UNKNOWN_OUTCOME',reason=type(exc).__name__+': '+str(exc))
        db.execute('UPDATE isolated_ifc_exports SET state=?,result=? WHERE operation_id=?',(result['status'],C.RUN.canonical(result),operation_id));db.commit()
    return result


def main(argv=None):
    import argparse,json
    p=argparse.ArgumentParser(description='Read actual local IFC quantities and semantic links, without native calls.')
    p.add_argument('--ifc',type=Path,required=True);p.add_argument('--native',type=Path)
    p.add_argument('--native-map',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(argv)
    if args.output.exists():raise ValueError('IFC_REPORT_REQUIRES_NEW_FILE')
    read=lambda path:json.loads(path.read_text(encoding='utf8')) if path else None
    result=inspect_quantified_exchange(args.ifc,read(args.native),read(args.native_map))
    C.A.write_json(args.output,result)
    print(C.RUN.canonical({'elements':len(result['elements']),'quantityMatchCount':result['quantityMatchCount'],
        'quantityMismatchCount':result['quantityMismatchCount'],'nativeWrites':0,'semanticCompatibility':'NOT_VERIFIED'}))
    return 0


if __name__=='__main__':raise SystemExit(main())
