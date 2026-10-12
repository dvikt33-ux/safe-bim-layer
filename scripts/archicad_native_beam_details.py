"""Native Beam recipes for source sections, over the existing SceneWriter.

Reuse the accepted measured roof/support geometry. The old Morph recipe is
only a coordinate source; no Morph operation is dispatched by this adapter.
"""
import copy
import math
import archicad_details_context as D
C=D.C


def require_morph_last_resort(dependencies):
    source=dependencies.get('sourceDetailBinding',{})
    if source.get('entityId') in ('c4','c5'):
        raise ValueError('NATIVE_BEAM_REQUIRED_FOR_SOURCE_RECTANGULAR_SECTION')
    assessment=dependencies.get('nativeToolAssessment',{})
    checks=assessment.get('checkedNativeTools')
    if (not isinstance(checks,list) or not checks or
            any(not isinstance(r,dict) or not r.get('tool') or not r.get('contractEvidence') or
                not r.get('geometryLimitation') for r in checks) or
            not assessment.get('reasonNativeGeometryImpossible') or
            assessment.get('mandatoryBimPropertiesAndRelationsPreserved') is not True):
        raise ValueError('MORPH_LAST_RESORT_NATIVE_TOOL_EVIDENCE_REQUIRED')
    return assessment


def prepare_beam(source,part,translation_x=0.,placement_authority=None):
    """Convert an existing planar rectangular source recipe to a real Beam.

    Native end cuts remain an independent readback obligation. Explicit
    dimensions/profile/anchor replace project defaults; no favorite changes.
    """
    binding=copy.deepcopy(part['binding'])
    if binding['entityId'] not in ('c4','c5'):raise ValueError('BEAM_SOURCE_ENTITY_UNSUPPORTED')
    if not math.isfinite(translation_x):raise ValueError('BEAM_TRANSLATION_INVALID')
    data=part['plan']['graph']['operations'][0]['params']['morphsData'][0]
    section=binding['sourceSectionMeters'];length=binding['modelDerivedLengthMeters']
    def world(x):
        p=C.morph_api_world_point({'x':x,'y':section['width']/2,'z':section['height']/2},
            data['basePoint'],[data[k] for k in ('xAxis','yAxis','zAxis')])
        return [p[0]+translation_x,p[1],p[2]]
    begin=world(0.);end=world(length)
    horizontal=math.hypot(end[0]-begin[0],end[1]-begin[1])
    if horizontal<=0:raise ValueError('BEAM_SOURCE_AXIS_NOT_SUPPORTED')
    slope=math.atan2(end[2]-begin[2],horizontal)
    # c4 axis is world X; its rectangular section follows the roof slope.
    # AC29 Beam profileAngle rotates opposite to the Morph matrix convention.
    profile=-math.atan2(data['zAxis']['y'],data['yAxis']['y']) if binding['entityId']=='c4' else 0.
    beam={'begCoordinate':dict(zip(('x','y'),begin[:2])),
        'endCoordinate':dict(zip(('x','y'),end[:2])),'zCoordinate':begin[2],
        'floorIndex':data['floorIndex'],'offset':0.,'slantAngle':slope,'isSlanted':abs(slope)>1e-9,
        'profileAngle':profile,'arcAngle':0.,'verticalCurveHeight':0.,
        'width':section['width'],'height':section['height'],'anchorPoint':'Center',
        'circleBased':False,'isWidthAndHeightLinked':False,
        'buildingMaterialId':copy.deepcopy(data['buildingMaterialId'])}
    binding.update(expectedNativeBeamParameters=copy.deepcopy(beam),nativeTool='Beam',
        geometryAuthority='Accepted planar source recipe and actual native roof/support span',
        placementAuthority=placement_authority or 'Accepted source recipe centerline',
        nativeEndCutAcceptance='REQUIRES_ACTUAL_SEGMENT_BODY_AND_CONTACT_READBACK')
    if binding['entityId']=='c5':
        contact=binding['physicalContact']
        contact['nominalPerpendicularEndContactAreaSquareMeters']=contact['expectedAreaSquareMeters']
        contact['expectedAreaSquareMeters']-=section['width']*section['height']/2*abs(math.tan(slope))
        contact['nativeEndCutAuthority']='Vertical native end plane at centerline begin; actual segment faces must confirm it'
    if translation_x and not placement_authority:raise ValueError('BEAM_TRANSLATION_AUTHORITY_REQUIRED')
    op={'id':'native-source-beam-'+binding['entityId'],'command':'CreateBeams','params':{'beamsData':[beam]}}
    plan=C.bind_plan(source,[op],['beam'],{'sourceBeamBinding':binding})
    return {'status':'OFFLINE_NATIVE_BEAM_SOURCE_GRAPH_PREPARED','binding':binding,'plan':plan,'nativeWrites':0}


def prepare_native_batten(root,source,context,native,host_guid,material_selection,placement_y=None):
    return prepare_beam(source,D.prepare_source_section(root,source,context,native,host_guid,'c4',material_selection,placement_y))


def prepare_native_counterbatten(root,source,context,native,batten_guid,end_wall_guid,translation_x=0.,placement_authority=None):
    return prepare_beam(source,D.prepare_counterbatten_junction(root,source,context,native,batten_guid,end_wall_guid),translation_x,placement_authority)


def verify_beam_binding(api,params,binding):
    D.verify_source_section_binding(api,binding)
    fact=C.details_candidate(__import__('pathlib').Path(__file__).resolve().parents[1],
        binding['detailId'],{'guid':binding['hostGuid'],'kind':'Roof'})
    rows=[r for r in fact['resolvedFacts'] if r['entity']==binding['entityId'] and r['fact']['fact_id']==binding['sourceFactId']]
    if len(rows)!=1 or binding['archiveSha256']!=C.DETAILS_SHA:
        raise ValueError('BEAM_SOURCE_FACT_INVALIDATED')
    section={'width':rows[0]['values']['value_2']/1000,'height':rows[0]['values']['value']/1000}
    if section!=binding['sourceSectionMeters']:raise ValueError('BEAM_SOURCE_DIMENSION_INVALIDATED')
    if params!={'beamsData':[binding['expectedNativeBeamParameters']]}:
        raise ValueError('BEAM_SOURCE_PARAMETERS_MISMATCH')
    return {'status':'NATIVE_BEAM_SOURCE_BINDING_PASS'}


def verify_contact(api,binding,parent_guid,counterpart_guids=None):
    """Actual segment solids/contact; never classify a Morph as native Beam."""
    D.verify_source_section_binding(api,binding)
    native=C.G.normalize_dump(api('GetModelDumpV1',{}));bodies={e['guid'].lower():e for e in native['elements']}
    parent=parent_guid.lower()
    if bodies[parent]['type']!='Beam':raise ValueError('NATIVE_BEAM_PARENT_REQUIRED')
    children=C.A.assembly_subelements(api,{'member':{'guid':parent,'kind':'Beam'}},'Beam')[parent]
    peers=counterpart_guids or [binding['physicalContact']['counterpartGuid'].lower()]
    if binding['entityId']=='c5' and not counterpart_guids:
        y=binding['expectedNativeBeamParameters']['begCoordinate']['y']
        if not any(all(C.RUN.close(solid['vertices'][i][1],y) for i in face['vertices']) and len(face['vertices'])>=4
                for g in children for solid in bodies[g]['bodies'] for face in solid['faces']):
            raise ValueError('NATIVE_BEAM_VERTICAL_END_PLANE_NOT_VERIFIED')
    contacts=C.G.shared_surfaces(bodies,{g:g for g in children+peers})
    area=sum(r['sharedAreaSquareMeters'] for r in contacts if any(g in children for g in r['guids']) and any(g in peers for g in r['guids']))
    expected=binding['physicalContact']['expectedAreaSquareMeters']
    if not C.RUN.close(area,expected,1e-6):raise ValueError('NATIVE_BEAM_ACTUAL_SUPPORT_AREA_MISMATCH:'+str(area))
    collision=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':parent}}],
        'elementsGroup2':[{'elementId':{'guid':g}} for g,e in bodies.items() if g not in [parent]+children and e.get('bodies')]})
    if collision.get('collisions')!=[]:raise ValueError('NATIVE_BEAM_UNPLANNED_VOLUME_COLLISION')
    return {'status':'LIVE_NATIVE_BEAM_SOURCE_CONTACT_PASS','nativeTool':'Beam','parentGuid':parent,
        'segmentGuids':children,'counterpartGuids':peers,'sharedAreaSquareMeters':area,
        'nominalPerpendicularEndContactAreaSquareMeters':binding['physicalContact'].get('nominalPerpendicularEndContactAreaSquareMeters',expected),
        'nativeEndCutScope':'Actual native end geometry; equivalence to original Morph end cut not claimed',
        'sourceSectionMeters':binding['sourceSectionMeters'],'nativeVolumeCollision':collision,
        'actualSegments':[{'guid':g,'bounds':C.ROOF.bounds(bodies[g]),'homeStory':bodies[g]['homeStory'],
            'materialBindings':bodies[g]['materialBindings'],'relationships':bodies[g]['relationships']} for g in children],
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED','completeManufacturerAssembly':'NOT_VERIFIED'}
