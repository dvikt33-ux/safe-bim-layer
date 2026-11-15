"""A02.S02: source/edition-aware requirement binding, no compliance solver."""
import copy,json
from collections import defaultdict
from itertools import pairwise
from pathlib import Path
import archicad_semantic_brief as BRIEF
import archicad_scene_run as RUN

CATALOG=Path(__file__).resolve().parents[1]/'examples/accelerator/ru-junction-rulepack-20261012.json'
SOURCE_CONDITIONS=CATALOG.with_name('verified-roof-source-conditions-20261012.json')

CERAMIC_1NF = {
    'profileId': 'ceramic-1nf-10-12',
    'brickLengthMM': 250, 'brickWidthMM': 120, 'brickHeightMM': 65,
    'verticalJointMM': 10, 'bedJointMM': 12,
    'references': [
        {'document': 'ГОСТ 530-2012', 'locator': 'Таблица 2, 1 НФ',
         'uri': 'https://protect.gost.ru/gost/details/e3f3ca57-13cb-493c-a047-21814635e7fc'},
        {'document': 'СП 70.13330.2012', 'locator': '9.2.4, до исключения изменением №8',
         'uri': 'https://protect.gost.ru/sp/details/2239acf1-711f-4f1f-aaa7-902fa06a8a60',
         'exclusionEffectiveDate': '2027-03-01'},
    ],
    'applicability': 'NOMINAL_COORDINATION_ONLY_PROJECT_NORMATIVE_APPLICABILITY_NOT_VERIFIED',
}


def wall_coordination_profile(selection, thickness):
    """Pin the selected nominal module to independent source references."""
    if (not isinstance(selection, dict) or selection.keys() != {'profileId', 'halfBrickUnitsAcross'}
            or selection['profileId'] != CERAMIC_1NF['profileId']
            or type(selection['halfBrickUnitsAcross']) is not int or selection['halfBrickUnitsAcross'] < 1):
        raise ValueError('WALL_COORDINATION_PROFILE_NOT_SUPPORTED')
    profile = copy.deepcopy(CERAMIC_1NF)
    count = selection['halfBrickUnitsAcross']
    plan = profile['brickWidthMM'] + profile['verticalJointMM']
    expected = count * plan - profile['verticalJointMM']
    mm = thickness * 1000
    if round(mm) != expected or abs(mm - round(mm)) > .001:
        raise ValueError('WALL_COORDINATION_THICKNESS_DOES_NOT_MATCH_PROFILE')
    profile.update(halfBrickUnitsAcross=count, nominalThicknessMM=expected,
                   planModuleMM=plan, courseModuleMM=profile['brickHeightMM'] + profile['bedJointMM'])
    return dict(profile, profileDigest=RUN.digest(profile))


def _wall_end_face(wall, members, coordinate_key, reference, *, sign):
    coordinate = wall[coordinate_key]
    if reference == '$wall-end':
        return coordinate
    host = members.get(reference, {})
    fixed = wall['constantCoordinate']
    clearance = wall['thicknessMeters'] / 2
    if (host.get('storyId') != wall['storyId'] or host.get('direction') == wall['direction']
            or abs(host['constantCoordinate'] - coordinate) > 1e-6
            or host['fromCoordinate'] > fixed - clearance + 1e-6
            or host['toCoordinate'] < fixed + clearance - 1e-6):
        raise ValueError('WALL_COORDINATION_REFERENCE_FACE_INVALID:' + wall['id'])
    return coordinate + sign * host['thicknessMeters'] / 2


def _nominal_row(length, profile):
    millimeters = length * 1000
    rounded = round(millimeters)
    modules, remainder = divmod(rounded + profile['verticalJointMM'], profile['planModuleMM'])
    fits = modules > 0 and remainder == 0 and abs(rounded - millimeters) <= .001
    return {'spanMM': round(millimeters, 3), 'status': 'NOMINAL_MODULE_MATCH' if fits else 'OFF_MODULE',
            **({'fullBrickEquivalents': modules // 2, 'halfModuleRemainder': modules % 2,
                'interiorJointEquivalents': (modules + 1) // 2 - 1} if fits else {})}


def wall_coordination_checks(members, candidates, openings):
    profiles = {row['id']: row['coordination'] for row in candidates if 'coordination' in row}
    if not profiles:
        return []
    openings_by_host = defaultdict(list)
    for opening in openings:
        openings_by_host[opening['hostMemberId']].append(opening)
    results = []
    for wall in members.values():
        candidate = wall['wallCseCandidateId']
        if candidate not in profiles:
            continue
        profile = profiles[candidate]
        row = dict(wallMemberId=wall['id'], cseCandidateId=candidate, profileDigest=profile['profileDigest'],
                   faceBasis='AUTHORED_NOMINAL_WALL_FACES', bond='NOT_VERIFIED',
                   lintels='NOT_VERIFIED', normativeApplicability='NOT_VERIFIED')
        results.append(row)
        if 'coordinationEnds' not in wall:
            row.update(status='REFERENCE_FACES_REQUIRED', checks=[])
            continue
        ends = wall['coordinationEnds']
        start = _wall_end_face(wall, members, 'fromCoordinate', ends['start'], sign=1)
        end = _wall_end_face(wall, members, 'toCoordinate', ends['end'], sign=-1)
        if end - start <= 1e-6:
            raise ValueError('WALL_COORDINATION_EMPTY_FACE_SPAN:' + wall['id'])
        checks = [dict(kind='WALL_FACE_SPAN', **_nominal_row(end - start, profile))]
        cuts = []
        for opening in openings_by_host[wall['id']]:
            left = wall['fromCoordinate'] + opening['centerOffset'] - opening['width'] / 2
            right = left + opening['width']
            if left < start - 1e-6 or right > end + 1e-6:
                raise ValueError('OPENING_OUTSIDE_COORDINATED_WALL_FACES:' + opening['id'])
            sill = opening['sillHeight']
            head = sill + opening['height']
            for key, level in [('SILL', sill), ('HEAD', head)]:
                mm = round(level * 1000)
                status = ('NOMINAL_MODULE_MATCH' if mm % profile['courseModuleMM'] == 0
                          and abs(level * 1000 - mm) <= .001 else 'OFF_MODULE')
                checks.append(dict(kind=key, openingId=opening['id'], levelMM=level * 1000, status=status))
            cuts.append((left, right, sill, head))
        levels = sorted({level for _, _, sill, head in cuts for level in (sill, head)})
        for low, high in pairwise(levels):
            active = sorted((left, right) for left, right, sill, head in cuts if sill < high and head > low)
            if not active:
                continue
            left_edges = [start] + [right for _, right in active]
            right_edges = [left for left, _ in active] + [end]
            for left, right in zip(left_edges, right_edges):
                if right - left > 1e-6:
                    checks.append(dict(kind='PIER_CLEAR_WIDTH', bandM=[low, high],
                                       **_nominal_row(right - left, profile)))
        row.update(status=('DESIGN_MODULE_MATCH' if all(c['status'] == 'NOMINAL_MODULE_MATCH' for c in checks)
                           else 'DESIGN_MODULE_CONFLICT'), wallFaceRangeM=[start, end],
                   endReferences=dict(ends), checks=checks)
    return results


def native_binding_signature(context,guids):
    elements={e['guid'].lower():e for e in context['elements'].values()}
    bodies={k.lower():v for k,v in context.get('nativeGeometrySignatures',{}).items()}
    return RUN.digest([{'element':elements[g.lower()],'bodySignature':bodies.get(g.lower())} for g in guids])


def compile_normative_pack(brief,project_pack,context,requirements,junctions,*,design_coordination=None):
    doc=BRIEF.normalize(brief)
    if (project_pack.get('projectId') != doc['projectId']
            or (context is None and (not design_coordination or junctions))
            or (context is not None and (context.get('units') != 'm'
                                        or context.get('coordinateSystem') != 'ABSOLUTE_PROJECT_XYZ'))):
        raise ValueError('NORMATIVE_PROJECT_OR_NATIVE_CONTEXT_MISMATCH')
    if not isinstance(requirements,dict) or set(requirements)-{'jurisdiction','projectFacts','cseFacts','requestedEditions'}:
        raise ValueError('NORMATIVE_REQUIREMENTS_FIELDS_INVALID')
    registry=json.loads(CATALOG.read_text(encoding='utf8'))
    if (registry['schema']!='APA_NORMATIVE_JUNCTION_CATALOG_V1' or
            any(d['clauseVerification']!='NOT_VERIFIED' for d in registry['documents'].values()) or
            any(r.get('numericRulesEnabled',False) for r in registry['rules']) or
            len({r['id'] for r in registry['rules']})!=len(registry['rules'])):
        raise ValueError('NORMATIVE_CATALOG_UNQUALIFIED')
    jurisdiction_input=requirements.get('jurisdiction') or {}
    if not isinstance(jurisdiction_input,dict):raise ValueError('NORMATIVE_JURISDICTION_REQUIRED')
    country=jurisdiction_input.get('country')
    jurisdiction=jurisdiction_input.get('evidenceUri')
    facts=requirements.get('projectFacts',{});systems=requirements.get('cseFacts',{});editions=requirements.get('requestedEditions',{})
    if any(not isinstance(v,dict) for v in (facts,systems,editions)):raise ValueError('NORMATIVE_FACT_MAPS_REQUIRED')
    elements={e['guid'].lower():e for e in (context or {}).get('elements', {}).values()};rows=[];seen=set()
    for target in junctions:
        if target['id'] in seen:raise ValueError('DUPLICATE_NORMATIVE_JUNCTION')
        seen.add(target['id']);guids=[g.lower() for g in target['guids']]
        if not guids or any(g not in elements for g in guids):raise ValueError('NORMATIVE_NATIVE_GUID_NOT_BOUND')
        selected=systems.get(target['id'],{})
        if not isinstance(selected,dict):raise ValueError('NORMATIVE_CSE_FACTS_REQUIRED')
        bodies={k.lower():v for k,v in context.get('nativeGeometrySignatures',{}).items()}
        body_bound=all(bodies.get(g) for g in guids)
        signature=native_binding_signature(context,guids)
        cse_current=(selected.get('nativeContextSignature')==signature and bool(selected.get('sourceEvidenceUri')))
        for rule in registry['rules']:
            document=registry['documents'][rule['document']];missing=[]
            family_matches=target['family'] in rule['families']
            status='NOT_VERIFIED' if family_matches else 'NOT_APPLICABLE'
            if family_matches:
                if country!='RU' or not jurisdiction:missing.append('PROJECT_JURISDICTION_NOT_VERIFIED')
                if editions.get(rule['document'],document['edition'])!=document['edition']:missing.append('REQUESTED_EDITION_DIFFERS_FROM_VERIFIED_REGISTRY')
                if not cse_current:missing.append('CSE_SOURCE_OR_NATIVE_SIGNATURE_NOT_BOUND')
                if not body_bound:missing.append('NATIVE_BODY_SIGNATURE_NOT_BOUND')
                for key in rule['requiredProjectFacts']:
                    if not isinstance(facts.get(key),dict) or not facts[key].get('evidenceUri'):missing.append('PROJECT_FACT:'+key)
                for key in rule['requiredCseFacts']:
                    if not selected.get(key):missing.append('CSE_FACT:'+key)
                # A known different system excludes this specific rule; an
                # unknown/misbound system never becomes NOT_APPLICABLE.
                predicate=rule.get('systemPredicate',{})
                if cse_current and body_bound and any(isinstance(selected.get(k),str) and selected[k] and selected[k]!=v for k,v in predicate.items()):
                    status='NOT_APPLICABLE'
                else:
                    if any(not isinstance(selected.get(k),str) or not selected[k] for k in predicate):missing.append('SYSTEM_SPECIFIC_APPLICABILITY_UNKNOWN')
                missing+=['ENGINEERING_EVIDENCE:'+key for key in rule['requiredEngineeringEvidence']]
                missing.append('FULL_CLAUSE_AND_SYSTEM_APPLICABILITY_NOT_VERIFIED')
            rows.append({'junctionId':target['id'],'nativeGuids':guids,'nativeContextSignature':signature,
                'family':target['family'],'ruleId':rule['id'],'edition':document['edition'],'sourceUri':document['uri'],
                'registryMetadata':document['metadataVerification'],'clauseLocator':rule['clauseLocator'],
                'status':status,'missingEvidence':missing,'numericEvaluationExecuted':False,
                'engineeringApproved':False,'geometryContactIsNotNormativeApproval':True})
    result={'schema':'APA_PROJECT_NORMATIVE_BINDINGS_V1','projectId':doc['projectId'],'nativeWriteCalls':0,
        'jurisdiction':copy.deepcopy(requirements.get('jurisdiction')),'registry':registry,
        'projectPackInputDigest':RUN.digest(project_pack),'briefInputDigest':RUN.digest(doc),
        'nativeContextDigest':RUN.digest(context) if context is not None else None,
        'requirementsDigest':RUN.digest(requirements),
        'junctionInputDigest':RUN.digest(junctions),'bindings':rows,
        'status':'SOURCE_LINKED_REQUIREMENTS_WITH_EXPLICIT_NOT_VERIFIED',
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED'}
    if design_coordination:
        result['designCoordination'] = copy.deepcopy(design_coordination)
        result['designEvaluation'] = 'NOMINAL_DIMENSIONS_CHECKED_NATIVE_AND_ENGINEERING_PENDING'
    result['normativePackDigest']=RUN.digest(result)
    return result


def evaluate_native_source_conditions(normative,context,native,requirements,junctions):
    """Verified source/scope checks. Document PASS never approves a roof."""
    import math
    import networkx as nx
    import archicad_native_operations as N
    if (normative.get('normativePackDigest')!=RUN.digest({k:v for k,v in normative.items() if k!='normativePackDigest'}) or
            normative.get('nativeContextDigest')!=RUN.digest(context) or normative.get('requirementsDigest')!=RUN.digest(requirements) or
            normative.get('junctionInputDigest')!=RUN.digest(junctions)):
        raise ValueError('SOURCE_CONDITION_INPUT_INVALIDATED')
    if native.get('units')!='m' or native.get('coordinateSystem')!='ABSOLUTE_PROJECT_XYZ':raise ValueError('SOURCE_CONDITION_NATIVE_METRES_REQUIRED')
    bodies={e['guid'].lower():e for e in native['elements']};guids=sorted({g.lower() for j in junctions for g in j['guids']})
    if any(g not in bodies for g in guids):raise ValueError('SOURCE_CONDITION_NATIVE_GUID_MISSING')
    actual=N.C.retained_geometry_signatures(native,guids)
    if any(actual[g]!=context.get('nativeGeometrySignatures',{}).get(g) for g in guids):raise ValueError('SOURCE_CONDITION_ACTUAL_BREP_INVALIDATED')
    source=json.loads(SOURCE_CONDITIONS.read_text(encoding='utf8'));s=source['sources'];graph=nx.DiGraph();rows=[];metrics={}
    facts=requirements.get('projectFacts',{});systems=requirements.get('cseFacts',{});jurisdiction=requirements.get('jurisdiction') or {}
    country=jurisdiction.get('country') if jurisdiction.get('evidenceUri') else None
    def fact(key,kind):
        entry=facts.get(key)
        if not isinstance(entry,dict) or not entry.get('evidenceUri'):return None
        value=entry.get('value')
        if kind=='number':return float(value) if type(value) in (int,float) and math.isfinite(value) and value>=0 else None
        return value if type(value) is kind else None
    for j in junctions:
        if j['family']!='wall_roof':continue
        roofs=[g.lower() for g in j['guids'] if bodies[g.lower()].get('type')=='Roof'];walls=[g for g in j['guids'] if bodies[g.lower()].get('type')=='Wall']
        if len(roofs)!=1 or len(walls)!=1:raise ValueError('SOURCE_CONDITION_NATIVE_WALL_ROOF_REQUIRED')
        roof=roofs[0];selected=systems.get(j['id'],{})
        bound=(selected.get('nativeContextSignature')==native_binding_signature(context,j['guids']) and bool(selected.get('sourceEvidenceUri')))
        technology=selected.get('roofSystem') if bound else None;work=fact('roofWorkType',str);missing=[]
        if country is None:missing.append('PROJECT_JURISDICTION_NOT_VERIFIED')
        if work not in s['roofScope']['allowedWorkTypes']:missing.append('ROOF_WORK_TYPE_NOT_VERIFIED')
        if technology not in s['roofScope']['allowedRoofSystems']:missing.append('SOURCE_BOUND_ROOF_TECHNOLOGY_NOT_VERIFIED')
        roof_edition_current=requirements.get('requestedEditions',{}).get('roof',normative['registry']['documents']['roof']['edition'])==s['roofScope']['edition']
        if not roof_edition_current:missing.append('ROOF_EDITION_NOT_BOUND_TO_VERIFIED_SOURCE')
        scope='NOT_VERIFIED'
        if country is not None and country!='RU':scope='NOT_APPLICABLE'
        elif not missing:scope='APPLICABLE'
        def row(rule,key,status,**extras):
            rows.append(dict(junctionId=j['id'],ruleId=rule,sourceId=key,status=status,nativeGuids=j['guids'],engineeringApproved=False,**extras))
        row('sp17-roof-scope','roofScope',scope,missingEvidence=missing)
        if roof not in metrics:
            try:
                plane=N.roof_underside_plane(bodies[roof]);n=plane['normal']
                metrics[roof]={'status':'VERIFIED_NATIVE_GEOMETRY','authority':plane['authority'],
                    'slopePercent':100*math.hypot(n[0],n[1])/abs(n[2]),'slopeDegrees':math.degrees(math.atan2(math.hypot(n[0],n[1]),abs(n[2]))),
                    'bodySignature':actual[roof],'normativeSlopeThreshold':None,'normativeSlopeResult':'NOT_VERIFIED'}
            except ValueError as error:metrics[roof]={'status':'NOT_VERIFIED','reason':str(error)}
        expected=s['roofThermalReference']['expectedThermalEdition']
        edition=requirements.get('requestedEditions',{}).get('thermal',normative['registry']['documents']['thermal']['edition'])
        row('sp17-amendment5-thermal-reference','roofThermalReference',('PASS_DOCUMENTED' if edition==expected else 'FAIL_DOCUMENT_REFERENCE') if roof_edition_current else 'NOT_VERIFIED',
            observedEdition=edition,expectedEdition=expected,roofApplicability=scope,
            acceptanceScope='Verified amendment reference edge only; not thermal or roof compliance')
        work=fact('buildingWorkType',str);use=fact('buildingUse',str);area=fact('totalBuildingAreaM2','number');regime=fact('maintainedTemperatureHumidity',bool)
        exclusions={k:fact('thermalExclusion:'+k,bool) for k in s['thermalScope']['exclusions']};historic=fact('architecturalHistoricSignificance',bool)
        values={'jurisdiction':country,'buildingWorkType':work,'buildingUse':use,'totalBuildingAreaM2':area,
            'maintainedTemperatureHumidity':regime,'architecturalHistoricSignificance':historic,**exclusions}
        missing=[key for key,value in values.items() if value is None];thermal='NOT_VERIFIED'
        if work is not None and work not in s['thermalScope']['allowedWorkTypes']:missing.append('BUILDING_WORK_TYPE_NOT_CLASSIFIED')
        if use is not None and use not in s['thermalScope']['allowedBuildingUses']:missing.append('BUILDING_USE_NOT_CLASSIFIED')
        thermal_current=edition==s['thermalScope']['edition']
        if not thermal_current:missing.append('THERMAL_EDITION_NOT_BOUND_TO_VERIFIED_SOURCE')
        if ((country is not None and country!='RU') or
                (area is not None and area<=s['thermalScope']['areaStrictlyGreaterThanM2']) or regime is False or any(v is True for v in exclusions.values())):
            thermal='NOT_APPLICABLE'
        elif historic is True:missing.append('HISTORIC_AUTHORITY_DECISION_REQUIRED')
        elif not missing:thermal='APPLICABLE'
        row('sp50-envelope-scope','thermalScope',thermal,missingEvidence=missing,totalBuildingAreaM2=area,areaIsNotInferredFromTestSlabs=True)
        for key in s:
            graph.add_edge('source:'+key,'roof:'+roof);graph.add_edge('roof:'+roof,'junction:'+j['id'])
    result={'schema':'APA_NATIVE_SOURCE_CONDITION_RESULTS_V1','sourceConditions':source,'sourceConditionsDigest':RUN.digest(source),
        'inputNormativePackDigest':normative['normativePackDigest'],'nativeMetrics':metrics,'checks':rows,
        'dependencyGraph':{'nodes':sorted(graph.nodes),'edges':[list(e) for e in sorted(graph.edges)],'acyclic':nx.is_directed_acyclic_graph(graph)},
        'nativeWriteCalls':0,'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED','technicalNormativeConditions':source['unavailableTechnicalClauses']}
    result['resultDigest']=RUN.digest(result);return result


def attach_to_project_pack(project_pack,normative):
    if (project_pack.get('projectId')!=normative.get('projectId') or
            RUN.digest(project_pack)!=normative.get('projectPackInputDigest') or
            normative.get('normativePackDigest')!=RUN.digest({k:v for k,v in normative.items() if k!='normativePackDigest'})):
        raise ValueError('NORMATIVE_PACK_INPUT_OR_RESULT_INVALIDATED')
    result=copy.deepcopy(project_pack);result['normativePackDigest']=normative['normativePackDigest']
    result['normativeRequirementBindings']=copy.deepcopy(normative['bindings'])
    return result


def evaluate_existing_machine_requirements(normative,context,requirements,junctions,
                                            source_checks,profile,**selection):
    """Use the mounted machine base through the existing normative contour."""
    import archicad_normative_machine as MACHINE
    return MACHINE.integrate_existing_machine(normative,context,requirements,junctions,
                                              source_checks,profile,**selection)
