"""Selected local GDL package, using the retained journal and SceneWriter.

No whole-library import, overwrite, global registry or second native writer.
Source licensing metadata and live native compatibility remain separate facts.
"""
from contextlib import closing
import copy, hashlib, sqlite3
from pathlib import Path
import archicad_project_accelerator as A
import archicad_authored_extension as E
import archicad_authored_geometry as G

def resolve(api,name,guid):
    result=api('GetAvailableLibraryParts',{'filterByTypeId':'Object'})
    rows=[r for r in result['libraryParts'] if r.get('documentName')==name]
    if len(rows)!=1 or rows[0].get('guid','').casefold()!=guid.casefold():
        raise ValueError('SELECTED_LIBRARY_NAME_OR_GUID_MISSING_OR_AMBIGUOUS')
    if rows[0].get('toolLookupError')!=0 or rows[0].get('toolType')!='Object':
        raise ValueError('SELECTED_LIBRARY_OBJECT_TOOL_UNVERIFIED')
    return {'part':rows[0],'skippedCount':result['skippedCount'],
            'completeCatalog':result['skippedCount']==0}

def import_selected(api,source,files,name,guid,journal,operation_id):
    if not A.RUN._SCENE_ID.fullmatch(operation_id) or not A.RUN._GUID.fullmatch(guid):
        raise ValueError('INVALID_SELECTED_LIBRARY_OPERATION')
    if not files or len(files)>10:raise ValueError('SELECTED_PACKAGE_SIZE_UNSUPPORTED')
    outputs=[f['outputPath'] for f in files]
    if len(set(outputs))!=len(outputs) or any(
            not p.startswith('APA_Selected_TN_20261011/') or '..' in Path(p).parts
            or Path(p).is_absolute() for p in outputs):
        raise ValueError('SELECTED_PACKAGE_OUTPUT_SCOPE_INVALID')
    hashes={f['inputPath']:hashlib.sha256(Path(f['inputPath']).read_bytes()).hexdigest() for f in files}
    binding=A.RUN.guarded_project(api,source['preflight']['storyBindings'][0])
    if binding!=source['preflight']['binding'] or binding['path']!=A.RUN.APPROVED_ISOLATED_WRITER_PATH:
        raise ValueError('SELECTED_LIBRARY_PROJECT_CHANGED')
    E.verify_model(api,source['preflight'],source['created'])
    if A.inventory_guids(api)!=source['inventory']:raise ValueError('SELECTED_LIBRARY_INVENTORY_DRIFT')
    catalog=api('GetAvailableLibraryParts',{'filterByTypeId':'Object'})
    if any(r.get('documentName')==name or r.get('guid','').casefold()==guid.casefold()
           for r in catalog['libraryParts']):raise ValueError('SELECTED_PART_ALREADY_PRESENT_NO_OVERWRITE')
    intent={'binding':binding,'files':files,'hashes':hashes,'name':name,'guid':guid,
            'inventory':source['inventory'],'overwriteExisting':False}
    with closing(sqlite3.connect(journal)) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS selected_library_imports(operation_id TEXT PRIMARY KEY,state TEXT,intent TEXT,result TEXT)')
        db.commit();db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO selected_library_imports VALUES(?,?,?,?)',
                   (operation_id,'ATTEMPTED',A.RUN.canonical(intent),'{}'));db.commit()
        result={'status':'PARTIAL_OR_UNKNOWN_OUTCOME','automaticRetry':False}
        try:
            if A.RUN.guarded_project(api,source['preflight']['storyBindings'][0])!=binding or A.inventory_guids(api)!=source['inventory']:
                raise ValueError('SELECTED_LIBRARY_OPERATION_BOUNDARY_DRIFT')
            if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):
                raise ValueError('SELECTED_LIBRARY_SOURCE_CHANGED')
            response=api('AddFilesToEmbeddedLibrary',{'files':files,'overwriteExisting':False})
            if response.get('executionResults')!=[{'success':True}]*len(files):
                raise ValueError('SELECTED_LIBRARY_IMPORT_NOT_CONFIRMED')
            selected=resolve(api,name,guid)
            if A.RUN.guarded_project(api,source['preflight']['storyBindings'][0])!=binding or A.inventory_guids(api)!=source['inventory']:
                raise ValueError('SELECTED_LIBRARY_IMPORT_GUID_OR_PROJECT_DRIFT')
            E.verify_model(api,source['preflight'],source['created'])
            result={'status':'SELECTED_LIBRARY_IMPORT_READBACK_PASS','selected':selected,
                    'response':response,'intent':intent,'automaticRetry':False}
        except Exception as exc:result['reason']=type(exc).__name__+': '+str(exc)
        db.execute('UPDATE selected_library_imports SET state=?,result=? WHERE operation_id=?',
                   (result['status'],A.RUN.canonical(result),operation_id));db.commit()
    return result

def prepare_object(api,source,name,guid,point,dimensions,step_id='selected-tn-aerator'):
    selected=resolve(api,name,guid)
    plan=copy.deepcopy(source['preflight'])
    if A.RUN.guarded_project(api,plan['storyBindings'][0])!=plan['binding']:
        raise ValueError('SELECTED_OBJECT_PROJECT_DRIFT')
    E.verify_model(api,plan,source['created'])
    if A.inventory_guids(api)!=source['inventory']:raise ValueError('SELECTED_OBJECT_INVENTORY_DRIFT')
    if set(point)!={'x','y','z'} or set(dimensions)!={'x','y','z'} or any(
            type(v) not in (int,float) or not A.RUN.math.isfinite(v) for v in point.values()) or any(
            type(v) not in (int,float) or not A.RUN.math.isfinite(v) or v<=0 for v in dimensions.values()):
        raise ValueError('SELECTED_OBJECT_COORDINATES_OR_SIZE_INVALID')
    # Archicad reports inverted empty boxes for child ColumnSegments. Prove
    # exact current ownership and actual segment bodies first, then retain
    # the parent Column boxes in the existing conservative clearance scan.
    children=A.column_subelements(api,source['created'])
    if children!=source['columnSegments']:raise ValueError('SELECTED_OBJECT_COLUMN_OWNERSHIP_DRIFT')
    native=G.normalize_dump(api('GetModelDumpV1',{}))
    by_guid={r['guid'].lower():r for r in native['elements']}
    child_ids={g.lower() for group in children.values() for g in group}
    for parent_guid,group in children.items():
        for child in group:
            row=by_guid.get(child.lower(),{})
            if not row.get('bodies') or row.get('relationships',{}).get('hostGuid','').casefold()!=parent_guid.casefold():
                raise ValueError('SELECTED_OBJECT_SEGMENT_GEOMETRY_OR_HOST_UNVERIFIED')
    def parent_scan(command,params):
        value=api(command,params)
        if command=='GetAllElements':
            return {'elements':[r for r in value['elements'] if r['elementId']['guid'].lower() not in child_ids]}
        return value
    A.RUN.scan_for_existing_geometry(parent_scan,point['x'],point['y'],
        {'xMin':point['x']-dimensions['x'],'xMax':point['x']+dimensions['x'],
         'yMin':point['y']-dimensions['y'],'yMax':point['y']+dimensions['y'],
         'zMin':point['z']-.01,'zMax':point['z']+dimensions['z']})
    if step_id in source['created']:raise ValueError('SELECTED_OBJECT_STEP_ALREADY_EXISTS')
    plan['graph']['operations'].append({'id':step_id,'command':'CreateObjects','params':{'objectsData':[
        {'libraryPartName':name,'coordinates':point,'dimensions':dimensions,'angle':0.0,'floorIndex':0}]}})
    plan.setdefault('nativeLibraryExpectations',{})[step_id]={'name':name,'guid':guid}
    checked=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(A.RUN.DEFAULT_SCENE_SCHEMA),plan['graph'],runtime_version=A.RUN.EXPECTED_TAPIR)
    if checked['status']!='PLAN_VALIDATED_OFFLINE':raise ValueError('SELECTED_OBJECT_GRAPH_REFUSED: '+checked['status'])
    plan['executionOrder']=checked['executionOrder'];plan['sourcePlanHash']=A.RUN.native_plan_hash(plan,checked['sourcePlanHash'])
    plan['metrics']['elementCount']=len(plan['graph']['operations'])
    plan['metrics']['nativeCommands']['CreateObjects']=1
    return {'preflight':plan,'created':copy.deepcopy(source['created']),
            'inventory':source['inventory'],'columnSegments':source['columnSegments'],
            'libraryBinding':selected,'selectedStep':step_id,'expectedLibraryGuid':guid}

def verify_object(api,prepared,created):
    sid=prepared['selectedStep'];row=A.RUN.requested_details(api,created[sid]['guid'])
    lib=row['details']['libPart'];own=lib.get('ownUnID',{})
    actual=own.get('guid') if isinstance(own,dict) else None
    if not isinstance(actual,str) or actual.casefold()!=prepared['expectedLibraryGuid'].casefold():
        raise ValueError('OBJECT_OWN_LIBRARY_GUID_READBACK_MISMATCH')
    E.verify_model(api,prepared['preflight'],created)
    if A.inventory_guids(api)!=sorted(prepared['inventory']+[created[sid]['guid'].lower()]):
        raise ValueError('SELECTED_OBJECT_WHOLE_INVENTORY_DIFF')
    return row

def verify_geometry(raw,guid,point,dimensions):
    model=G.normalize_dump(raw)
    rows=[r for r in model['elements'] if r['guid'].casefold()==guid.casefold()]
    if len(rows)!=1 or rows[0]['type']!='Object' or rows[0]['homeStory']!=0:
        raise ValueError('SELECTED_OBJECT_NATIVE_DUMP_IDENTITY_MISMATCH')
    target=rows[0];vertices=[p for b in target['bodies'] for p in b['vertices']]
    if not vertices:raise ValueError('SELECTED_OBJECT_NATIVE_GEOMETRY_EMPTY')
    bounds={axis:[min(p[i] for p in vertices),max(p[i] for p in vertices)] for i,axis in enumerate('xyz')}
    if any(not A.RUN.close(sum(bounds[a])/2,point[a]) or not A.RUN.close(bounds[a][1]-bounds[a][0],dimensions[a]) for a in 'xy'):
        raise ValueError('SELECTED_OBJECT_NATIVE_XY_SIZE_OR_CENTER_MISMATCH')
    if not A.RUN.close(bounds['z'][0],point['z']) or not 0<bounds['z'][1]-bounds['z'][0]<=dimensions['z']+1e-5:
        raise ValueError('SELECTED_OBJECT_NATIVE_Z_ENVELOPE_MISMATCH')
    return {'bodies':len(target['bodies']),'vertices':len(vertices),'bounds':bounds,
            'parameterHeight':dimensions['z'],'physicalHeight':bounds['z'][1]-bounds['z'][0],
            'parameterHeightEqualsPhysicalHeight':A.RUN.close(dimensions['z'],bounds['z'][1]-bounds['z'][0])}
