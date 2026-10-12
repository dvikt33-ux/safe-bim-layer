"""Read-only shared acceptance of a journaled functional gap package.

The receipt binds prior accepted core, verified new identities, expected bodies
and original GUIDs. It never dispatches Create/Modify or trusts generic MEP
enumeration as completeness. Writes stay in SceneWriter.
"""
import argparse,json
from pathlib import Path
import archicad_details_context as D
import archicad_native_mep_network as M
import archicad_native_operations as O
C=O.C


def inspect_package(api,receipt,root):
    context,native=C.native_context(api,receipt['source'],receipt['connectedPlan'],receipt['connectedCreated'])
    actual=C.retained_geometry_signatures(native,receipt['originalGuids'])
    if actual!=receipt['originalGeometrySignatures']:raise ValueError('ORIGINAL_NATIVE_GEOMETRY_DRIFT')
    if context['inventory']!=receipt['inventory']:raise ValueError('PACKAGE_INVENTORY_DRIFT')
    network=M.read_network(api,receipt['routeGuids'],receipt['systemGuid'])
    if not network['logicalConnected'] or not network['physicalConnected']:raise ValueError('PACKAGE_MEP_NETWORK_DISCONNECTED')
    for sid,guid in receipt['newPrimaryGuids'].items():
        row=C.RUN.requested_details(api,guid);body=O.element_body(api,guid)
        context['elements'][sid]={'guid':guid,'kind':row['type'],'floorIndex':row['floorIndex'],
            'bounds':[body['bounds']],'materialBindings':body['native'].get('materialBindings',{}),
            'hostGuid':receipt.get('hosts',{}).get(guid)}
    for route in network['routes']:
        guid=route['guid'];matches=[sid for sid,e in context['elements'].items() if e['guid'].lower()==guid.lower()]
        sid=matches[0] if matches else 'mep-extension-'+guid.lower()
        if not matches:
            native_story=C.RUN.requested_details(api,guid).get('floorIndex')
            if native_story not in {s['nativeIndex'] for s in context['storyBindings']}:raise ValueError('MEP_NATIVE_STORY_NOT_BOUND')
            context['elements'][sid]={'guid':guid,'kind':'MEPRouting','floorIndex':native_story,
                'bounds':[],'materialBindings':{},'hostGuid':None}
        ends=[route['details']['polyline'][0],route['details']['polyline'][-1]]
        physical=[g for g in network['physicalGuids'] if all(any(p['ownerGuid']==g and C.points_equal(p['position'],end) for p in network['ports']) for end in ends)]
        if len(physical)!=1:raise ValueError('PHYSICAL_ROUTE_MAPPING_AMBIGUOUS')
        C.attach_physical_route(api,context,native,sid,{'physicalElementGuid':physical[0],'evidence':network['nativeTopologyAuthority']})
    opening=O.opening_readback(api,receipt['openingGuid'],receipt['openingHostGuid'],receipt['beforeOpeningHost'],receipt.get('openingParameters'))
    seo=O.seo_readback(api,receipt['seoTargetGuid'],receipt['seoOperatorGuid'],receipt['beforeSEOTarget'],receipt['seoBounds'])
    # Opening generic details are incomplete; native host relation and its actual
    # cut body remain authoritative. Do not invent an Opening body when omitted.
    context['elements']['generic-opening']={'guid':receipt['openingGuid'],'kind':'Opening',
        'floorIndex':opening['homeStory'],'bounds':[opening['nativeHoleBoundsMeters']] if 'nativeHoleBoundsMeters' in opening else [],
        'materialBindings':{},'hostGuid':receipt['openingHostGuid'],'geometryAuthority':opening.get('geometryAuthority','NOT_VERIFIED')}
    details=D.DetailsContext(root).evaluate(context,receipt.get('productBindings'))
    roof=next(e for e in context['elements'].values() if e['kind']=='Roof')
    manufacturer=C.details_candidate(root,'ARMO_SELFLOCK_ROOF__P0003',roof)
    collision=api('GetCollisions',{'elementsGroup1':[{'elementId':{'guid':g}} for g in network['physicalGuids']],
        'elementsGroup2':[{'elementId':{'guid':v['guid']}} for v in context['elements'].values() if v['kind'] not in ('MEPRouting','Opening')]})
    if not isinstance(collision.get('collisions'),list):raise ValueError('COLLISION_RESPONSE_INVALID')
    if collision['collisions']:raise ValueError('NEW_NETWORK_ARCHITECTURAL_COLLISION')
    return {'status':'LIVE_FUNCTIONAL_PACKAGE_READBACK_PASS','context':context,'network':network,
        'details':details,'manufacturer':manufacturer,'opening':opening,'seo':seo,
        'collisionReadback':collision,'providerScope':O.provider_scope(C.A.catalog_with_provenance(C.RUN.DEFAULT_SCENE_SCHEMA)),
        'originalGuidCount':len(receipt['originalGuids']),'inventoryCount':len(context['inventory']),
        'modelWrites':0,'engineeringAcceptance':'NOT_VERIFIED'},native


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(argv);receipt=json.loads(args.receipt.read_text(encoding='utf8'))
    C.RUN.bind_isolated_writer_pln(19724);args.output.mkdir(parents=True,exist_ok=False)
    api=C.A.EvidenceAPI(C.A.native_transport,args.output)
    api.allowed|={'GetMEPRoutingElements','GetMEPDistributionSystems','GetMEPPorts','GetMEPElements','GetConnectedElements','GetSolidElementLinks','GetCollisions','GetIFCIdsOfElements'}
    result,native=inspect_package(api,receipt,Path(__file__).resolve().parents[1]);C.A.write_json(args.output/'result.json',result);C.A.write_json(args.output/'normalized.json',native)
    print(C.RUN.canonical({k:result[k] for k in ['status','originalGuidCount','inventoryCount','engineeringAcceptance']}));return 0


if __name__=='__main__':raise SystemExit(main())
