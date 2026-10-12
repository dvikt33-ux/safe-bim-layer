"""A02.S02: source/edition-aware requirement binding, no compliance solver."""
import copy,json
from pathlib import Path
import archicad_semantic_brief as BRIEF
import archicad_scene_run as RUN

CATALOG=Path(__file__).resolve().parents[1]/'examples/accelerator/ru-junction-rulepack-20261012.json'


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


def attach_to_project_pack(project_pack,normative):
    if (project_pack.get('projectId')!=normative.get('projectId') or
            RUN.digest(project_pack)!=normative.get('projectPackInputDigest') or
            normative.get('normativePackDigest')!=RUN.digest({k:v for k,v in normative.items() if k!='normativePackDigest'})):
        raise ValueError('NORMATIVE_PACK_INPUT_OR_RESULT_INVALIDATED')
    result=copy.deepcopy(project_pack);result['normativePackDigest']=normative['normativePackDigest']
    result['normativeRequirementBindings']=copy.deepcopy(normative['bindings'])
    return result
