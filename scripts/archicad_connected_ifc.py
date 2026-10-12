"""Local IFC coordination/export over the shared native context.

Exports stay local. Aggregate route IDs may differ from the exported physical
duct's IFC root: missing mappings are reported rather than silently matched.
"""
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
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
        if element is None and native.get('physicalIfcId'):
            try:element=model.by_guid(native['physicalIfcId'])
            except RuntimeError:element=None
            if element:
                physical=True
                row.update(aggregateIfcIdNotExported=identifier,physicalIfcId=native['physicalIfcId'],
                    physicalNativeGuid=native['physicalElementGuid'],mappingScope='EXPORTED_PHYSICAL_DUCT; CONTAINER_IS_NOT_AN_IFC_ROOT')
        if element:
            row.update(ifcType=element.is_a(),status='IFC_IDENTITY_MAPPED')
            try:
                shape=ifcopenshell.geom.create_shape(settings,element)
                v=shape.geometry.verts
                points=[v[i:i+3] for i in range(0,len(v),3)]
                if not points:raise ValueError('EMPTY_IFC_SHAPE')
                bounds=[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(3)]
                source_bounds=native['physicalBounds'] if physical else native['bounds']
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
