"""A02.S02: source/edition-aware requirement binding, no compliance solver."""
import copy,json
from pathlib import Path
import archicad_semantic_brief as BRIEF
import archicad_scene_run as RUN

CATALOG=Path(__file__).resolve().parents[1]/'examples/accelerator/ru-junction-rulepack-20261012.json'
SOURCE_CONDITIONS=CATALOG.with_name('verified-roof-source-conditions-20261012.json')


def native_binding_signature(context,guids):
    elements={e['guid'].lower():e for e in context['elements'].values()}
    bodies={k.lower():v for k,v in context.get('nativeGeometrySignatures',{}).items()}
    return RUN.digest([{'element':elements[g.lower()],'bodySignature':bodies.get(g.lower())} for g in guids])


def compile_normative_pack(brief,project_pack,context,requirements,junctions):
    doc=BRIEF.normalize(brief)
    if project_pack.get('projectId')!=doc['projectId'] or context.get('units')!='m' or context.get('coordinateSystem')!='ABSOLUTE_PROJECT_XYZ':
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
    elements={e['guid'].lower():e for e in context['elements'].values()};rows=[];seen=set()
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
        'nativeContextDigest':RUN.digest(context),'requirementsDigest':RUN.digest(requirements),
        'junctionInputDigest':RUN.digest(junctions),'bindings':rows,
        'status':'SOURCE_LINKED_REQUIREMENTS_WITH_EXPLICIT_NOT_VERIFIED',
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED'}
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
