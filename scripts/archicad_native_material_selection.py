"""Project-local typed selection, reusing the Template Builder headers.

This is a bounded adapter for existing elements, not a new materials database
or native writer. Construction/normative adequacy and distribution rights are
separate from native attribute identity and successful application.
"""
import copy,math
import archicad_project_accelerator as A
import archicad_template_builder as T

DETAIL_COMMANDS={'BuildingMaterial':('GetBuildingMaterials','buildingMaterials'),
 'Composite':('GetComposites','composites'),'Profile':('GetProfiles','profiles'),
 'Surface':('GetSurfaces','surfaces')}

def resolve(api,kind,name,expected_guid):
    if kind not in DETAIL_COMMANDS or not isinstance(name,str) or not name or not isinstance(expected_guid,str) or not A.RUN._GUID.fullmatch(expected_guid):
        raise ValueError('INVALID_TYPED_ATTRIBUTE_SELECTION')
    class Headers:
        def call(self,command,params):return api(command,params)
    rows=T.attribute_headers(Headers(),kind)
    matches=[r for r in rows if r.get('name')==name]
    if len(matches)!=1:raise ValueError('ATTRIBUTE_NAME_MISSING_OR_AMBIGUOUS')
    header=matches[0]
    if header['attributeId']['guid'].casefold()!=expected_guid.casefold():
        raise ValueError('PROJECT_ATTRIBUTE_GUID_MISMATCH')
    command,key=DETAIL_COMMANDS[kind]
    rows=api(command,{'attributeIds':[{'attributeId':header['attributeId']}]})[key]
    if len(rows)!=1 or rows[0].get('attributeId',{}).get('guid','').casefold()!=expected_guid.casefold() or rows[0].get('name')!=name:
        raise ValueError('ATTRIBUTE_DETAIL_IDENTITY_MISMATCH')
    return rows[0]

def skin_materials(attribute):
    rows=attribute.get('skins')
    if not isinstance(rows,list) or not rows:raise ValueError('ATTRIBUTE_SKINS_MISSING')
    guids=[r.get('buildingMaterialId',{}).get('attributeId',{}).get('guid','') for r in rows]
    if any(not A.RUN._GUID.fullmatch(g) for g in guids):raise ValueError('SKIN_MATERIAL_IDENTITY_MISSING')
    return guids

def profile_area(attribute):
    from shapely.geometry import Polygon
    area=0
    for skin in attribute['skins']:
        if skin.get('outlineArcs'):raise ValueError('CURVED_PROFILE_OUTLINE_UNSUPPORTED')
        coords=skin.get('outlineCoords',[]);ends=skin.get('outlineSubPolyEnds',[])
        if not coords or len(ends)<2 or ends[0]!=0 or ends[-1]!=len(coords)-1:
            raise ValueError('PROFILE_OUTLINE_INDEX_COVERAGE_MISSING')
        contours=[[(v['x'],v['y']) for v in coords[start+1:end+1]] for start,end in zip(ends,ends[1:])]
        polygon=Polygon(contours[0],contours[1:])
        if not polygon.is_valid or polygon.area<=0:raise ValueError('PROFILE_OUTLINE_INVALID')
        area+=polygon.area
    return area

def compile_change(api,plan,created,step_id,selection):
    if set(selection)!={'kind','name','expectedGuid'}:raise ValueError('MATERIAL_SELECTION_CONTRACT_MISMATCH')
    changed=copy.deepcopy(plan)
    step=next((s for s in changed['graph']['operations'] if s['id']==step_id),None)
    if step is None or step_id not in created:raise ValueError('MATERIAL_CHANGE_UNKNOWN_OWNED_STEP')
    data=next(iter(step['params'].values()))[0]
    selected=resolve(api,selection['kind'],selection['name'],selection['expectedGuid'])
    target=created[step_id]['guid'];kind=selection['kind']
    if kind=='Composite' and step['command']=='CreateWalls':
        if 'Wall' not in selected.get('useWith',[]):raise ValueError('COMPOSITE_NOT_USABLE_WITH_WALL')
        skin_materials(selected)
        if any(type(s.get('thickness')) not in (int,float) or not math.isfinite(s['thickness']) or s['thickness']<=0 for s in selected['skins']):
            raise ValueError('COMPOSITE_SKIN_THICKNESS_INVALID')
        total=sum(s['thickness'] for s in selected['skins'])
        if not math.isfinite(total) or not A.RUN.close(total,data['thickness'],1e-6):
            raise ValueError('COMPOSITE_THICKNESS_CHANGES_ARCHITECTURAL_ENVELOPE')
        data.pop('buildingMaterialId',None);data.update(structureType='Composite',compositeId=selected['attributeId'])
        command='ModifyWalls';params={'wallsWithDetails':[{'elementId':{'guid':target},'structureType':'Composite','compositeId':selected['attributeId']}]}
    elif kind=='Surface' and step['command']=='CreateWalls':
        override={'overridden':True,'attributeId':selected['attributeId']}
        # Installed CreateWalls has no surface field. Keep its validated graph
        # intact; bind the explicit ModifyWalls readback expectation separately.
        changed.setdefault('nativeAttributeExpectations',{})[step_id]={'referenceMaterial':override}
        command='ModifyWalls';params={'wallsWithDetails':[{'elementId':{'guid':target},'referenceMaterial':override}]}
    elif kind=='Profile' and step['command']=='CreateColumns':
        if 'Column' not in selected.get('useWith',[]) or selected.get('widthStretchable') or selected.get('heightStretchable'):
            raise ValueError('PROFILE_REQUIRES_UNSUPPORTED_STRETCH_CONTRACT')
        if not all(type(selected.get(k)) in (int,float) and math.isfinite(selected[k]) and 0<selected[k]<=data[limit] for k,limit in [('width','width'),('height','depth')]):
            raise ValueError('PROFILE_OUTSIDE_APPROVED_COLUMN_ENVELOPE')
        skin_materials(selected);profile_area(selected)
        data.pop('buildingMaterialId',None);data.update(profileId=selected['attributeId'],width=selected['width'],depth=selected['height'])
        command='ModifyColumns';params={'columnsWithDetails':[{'elementId':{'guid':target},'profileId':selected['attributeId'],
            'isWidthAndHeightLinked':False,'width':selected['width'],'depth':selected['height'],'coreAnchor':'Center'}]}
    else:raise ValueError('UNSUPPORTED_ATTRIBUTE_EDIT_TARGET')
    compiled=A.SCENE.GRAPH.compile_graph(A.catalog_with_provenance(A.RUN.DEFAULT_SCENE_SCHEMA),changed['graph'],runtime_version=A.RUN.EXPECTED_TAPIR)
    if compiled['status']!='PLAN_VALIDATED_OFFLINE':raise ValueError('MATERIAL_EDIT_GRAPH_REFUSED')
    changed['sourcePlanHash']=A.RUN.native_plan_hash(changed,compiled['sourcePlanHash'])
    return {'newPlan':changed,'command':command,'parameters':params,'selected':selected,'stepId':step_id,
        'rights':'PROJECT_NATIVE_USE_ONLY_DISTRIBUTION_NOT_VERIFIED','engineeringAcceptance':'NOT_VERIFIED'}

def verify_selected_geometry(normalized,created,step_id,selected,children):
    """Check actual native profile cross-section, not only an AABB."""
    from shapely.geometry import Polygon
    guid=created[step_id]['guid'].lower();elements={r['guid'].lower():r for r in normalized['elements']}
    if elements[guid]['type']!=created[step_id]['kind'] or elements[guid]['homeStory']!=created[step_id]['floorIndex']:
        raise ValueError('SELECTED_DUMP_TYPE_OR_STORY_MISMATCH')
    for child in children.get(guid,[]):
        if elements[child]['type']!='ColumnSegment' or elements[child].get('relationships',{}).get('hostGuid','').casefold()!=guid:
            raise ValueError('SELECTED_SEGMENT_NATIVE_OWNER_MISMATCH')
    members=[elements[guid]]+[elements[g] for g in children.get(guid,[])]
    points=[p for r in members for body in r['bodies'] for p in body['vertices']]
    if not points:raise ValueError('SELECTED_ELEMENT_NATIVE_BODIES_MISSING')
    result={'nativeBodyCount':sum(len(r['bodies']) for r in members),'guid':guid}
    if 'skins' in selected and 'coluType' not in selected:
        composite=elements[guid].get('materialBindings',{}).get('composite',{})
        if composite.get('guid','').casefold()!=selected['attributeId']['guid'].casefold():
            raise ValueError('COMPOSITE_NATIVE_BINDING_MISMATCH')
        actual=composite.get('skins',[])
        if len(actual)!=len(selected['skins']) or any(
                a.get('buildingMaterial',{}).get('guid','').casefold()!=s['buildingMaterialId']['attributeId']['guid'].casefold()
                or not A.RUN.close(a.get('thickness'),s['thickness'],1e-6) for a,s in zip(actual,selected['skins'])):
            raise ValueError('COMPOSITE_NATIVE_SKIN_ORDER_OR_MATERIAL_MISMATCH')
        result['nativeCompositeSkins']=actual
    elif 'surfaceColor' in selected:
        binding=elements[guid].get('materialBindings',{}).get('refMat',{})
        if binding.get('overridden') is not True or binding.get('guid','').casefold()!=selected['attributeId']['guid'].casefold():
            raise ValueError('SURFACE_NATIVE_OVERRIDE_MISMATCH')
        result['nativeSurfaceOverride']=binding
    if 'coluType' in selected:
        for r in members:
            if r['bodies'] and r.get('materialBindings',{}).get('profile',{}).get('guid','').casefold()!=selected['attributeId']['guid'].casefold():
                raise ValueError('PROFILE_NATIVE_BINDING_MISMATCH')
        width=max(p[0] for p in points)-min(p[0] for p in points);depth=max(p[1] for p in points)-min(p[1] for p in points)
        if not A.RUN.close(width,selected['width'],1e-6) or not A.RUN.close(depth,selected['height'],1e-6):
            raise ValueError('PROFILE_NATIVE_XY_EXTENT_MISMATCH')
        top=max(p[2] for p in points);area=0
        for r in members:
            for body in r['bodies']:
                for face in body['faces']:
                    rings=[[body['vertices'][i] for i in c] for c in face['contours']]
                    if all(abs(p[2]-top)<1e-6 for ring in rings for p in ring):
                        polygon=Polygon([(p[0],p[1]) for p in rings[0]],
                            [[(p[0],p[1]) for p in ring] for ring in rings[1:]])
                        if not polygon.is_valid:raise ValueError('INVALID_PROFILE_NATIVE_TOP_FACE')
                        area+=polygon.area
        if not A.RUN.close(area,profile_area(selected),1e-8):raise ValueError('PROFILE_NATIVE_CROSS_SECTION_AREA_MISMATCH')
        result.update(width=width,depth=depth,topCrossSectionArea=area,profileOutlineArea=profile_area(selected))
    return result

def verify_library_bindings(api,created):
    catalogs={};bindings={}
    for sid,value in created.items():
        kind=value['kind']
        if kind not in ('Door','Window'):continue
        if kind not in catalogs:catalogs[kind]=api('GetAvailableLibraryParts',{'filterByTypeId':kind})
        part=A.RUN.requested_details(api,value['guid'])['details']['libPart']
        guid=part['ownUnID']['guid'];name=part['name']
        rows=[r for r in catalogs[kind]['libraryParts'] if r['guid'].casefold()==guid.casefold() and r['documentName']==name and r['typeId']==kind]
        if len(rows)!=1:raise ValueError('SELECTED_LIBRARY_PART_IDENTITY_NOT_UNIQUE')
        if rows[0].get('toolLookupError')!=0:raise ValueError('SELECTED_LIBRARY_TOOL_IDENTITY_UNVERIFIED')
        bindings[sid]={'nativeElementGuid':value['guid'],'libraryPart':part,'catalogEntry':rows[0],
            'inventorySkippedCount':catalogs[kind]['skippedCount'],
            'rights':'EXISTING_PROJECT_REFERENCE_ONLY_DISTRIBUTION_NOT_VERIFIED',
            'archicad29NativeInstanceReadback':True}
    return bindings
