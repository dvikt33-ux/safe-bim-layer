"""Bridge to the existing TDK machine base, not a second normative evaluator.

The byte-exact source slice supplies routing, blocks, rules and evidence gates.
Narrative calculators are never executed or inferred from their names.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import yaml
import archicad_normative_bindings as BIND
import archicad_scene_run as RUN

SOURCE = Path(__file__).resolve().parents[1] / 'vendor/tdk-normative-roof'
COMMIT = '67f17d407d14aebb091daaf79f11c10178b87440'
LOCK_SHA256 = 'e83a2c9b2e84f8208b4628a9cd5635dbb152cd29a60407fdcdae901f08576c75'
MACHINE = '01_Normative_Base/_Machine/'
BOOTSTRAP = ['NORMATIVE_WORK_PROTOCOL.md'] + [MACHINE+p for p in
    ('source_policy.yaml', 'rule.schema.yaml', 'README.md', 'TRUST_STATUS.md',
     'project_profile.schema.yaml', 'object_taxonomy.yaml', 'module_taxonomy.yaml',
     'retrieval_policy.yaml', 'dependency_resolution_policy.yaml', 'routes/index.yaml')]


class ExistingMachineSource:
    def __init__(self, root=SOURCE):
        self.root = Path(root).resolve()
        raw_lock = (self.root/'SOURCE_LOCK.json').read_bytes()
        if hashlib.sha256(raw_lock).hexdigest() != LOCK_SHA256:
            raise ValueError('MACHINE_SOURCE_LOCK_BYTES_CHANGED')
        self.lock = json.loads(raw_lock.decode('utf8'))
        if (self.lock.get('schema') != 'APA_EXISTING_NORMATIVE_SOURCE_LOCK_V1' or
                self.lock.get('repository') != 'dvikt33-ux/tdk-course-project' or
                self.lock.get('commit') != COMMIT or self.lock.get('authoritativeUse') is not False):
            raise ValueError('MACHINE_SOURCE_LOCK_INVALID')
        self.opened = []
        # Protocol first, policy/schema/README before normative interpretation.
        for path in BOOTSTRAP:
            self.read(path)

    def read(self, path):
        relative = Path(path)
        if relative.is_absolute():
            try: relative = relative.resolve().relative_to(self.root)
            except ValueError: raise ValueError('MACHINE_SOURCE_PATH_ESCAPE') from None
        key = relative.as_posix()
        if '..' in relative.parts or key not in self.lock['files']:
            raise ValueError('MACHINE_SOURCE_NOT_PINNED')
        target = (self.root/relative).resolve()
        if not target.is_relative_to(self.root): raise ValueError('MACHINE_SOURCE_PATH_ESCAPE')
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != self.lock['files'][key]['sha256']:
            raise ValueError('MACHINE_SOURCE_BYTES_CHANGED')
        if key not in self.opened: self.opened.append(key)
        return raw.decode('utf8')

    def data(self, path):
        return yaml.safe_load(self.read(path)) or {}

    def module(self, path, name):
        self.read(path)
        spec = importlib.util.spec_from_file_location(name, self.root/path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def resolve(self, object_type, module, depth, subject, inputs):
        route = self.data(MACHINE+'routes/objects/'+object_type+'.yaml')
        refs = route.get('compiled_blocks', {}).get(module, {}).get(depth, [])
        if not refs:
            return {'status':'MODULE_DEPTH_NOT_IMPLEMENTED', 'normative_authority':False}, [], route
        # Subject is explicit. Never find similarly named rules in other modules.
        targets = [self.data(p) for p in refs]
        targets = [b for b in targets if subject in b.get('object_scope', {}).get('functions', [])
            and b.get('source_pack_ref', {}).get('primary_rule_file') == MACHINE+'rules/roofing_2026.yaml']
        if not targets:
            return {'status':'SUBJECT_BLOCK_NOT_IMPLEMENTED', 'normative_authority':False}, [], route
        catalog = self.data(route['block_catalog'])['implemented_blocks']
        allowed = set()
        def include(bid):
            if bid in allowed: return
            if bid not in catalog: raise ValueError('MACHINE_BLOCK_DEPENDENCY_MISSING')
            allowed.add(bid)
            for dep in catalog[bid].get('requires', []): include(dep)
        for b in targets: include(b['block_id'])
        upstream = self.module('04_Code_Generation/runtime/block_resolver.py', 'apa_tdk_block_resolver')
        upstream._load_yaml = lambda path: self.data(path)
        # Keep upstream resolver/guards/closure. Limit its eager catalog load to
        # selected dependencies; inactive engineering blocks are never opened.
        class ScopedResolver(upstream.CompiledBlockResolver):
            def _load_blocks(instance):
                instance.catalog = copy.deepcopy(instance.catalog)
                instance.catalog['implemented_blocks'] = {k:v for k,v in
                    instance.catalog['implemented_blocks'].items() if k in allowed}
                super()._load_blocks()
        resolver = ScopedResolver(self.root, object_type)
        result = resolver.resolve({'explicit_blocks':[b['block_id'] for b in targets], 'runtime_inputs':inputs})
        return result, targets, route


def _profile_errors(profile, source, module, subject):
    schema = source.data(MACHINE+'project_profile.schema.yaml')
    errors = ['PROFILE:'+k for k in schema['project_profile']['required'] if k not in profile]
    taxonomy = source.data(MACHINE+'object_taxonomy.yaml')['object_classes']
    cls, sub = profile.get('object_class'), profile.get('object_subclass')
    if cls not in taxonomy or sub not in taxonomy.get(cls, {}).get('children', {}):
        errors.append('EXACT_OBJECT_PROFILE_REQUIRED')
    if not profile.get('evidenceUri'): errors.append('PROJECT_TYPE_EVIDENCE_REQUIRED')
    if profile.get('jurisdiction') != 'RU': errors.append('JURISDICTION_NOT_BOUND')
    if profile.get('project_phase') not in ('concept', 'design', 'working_documentation', 'reconstruction'):
        errors.append('PROJECT_STAGE_REQUIRED')
    functions = profile.get('active_functions')
    if not isinstance(functions, list) or any(not isinstance(v,str) for v in functions):
        errors.append('ACTIVE_FUNCTIONS_REQUIRED')
    modules = profile.get('modules', {})
    taxonomy = source.data(MACHINE+'module_taxonomy.yaml')['modules']
    if not isinstance(modules, dict): return errors+['MODULE_MAP_REQUIRED']
    for key, depth in modules.items():
        levels = ['off' if v is False else v for v in taxonomy.get(key, {}).get('depth_levels', [])]
        if key not in taxonomy or depth not in levels: errors.append('MODULE_DEPTH_INVALID:'+key)
    if module not in modules or modules[module] == 'off': errors.append('REQUESTED_MODULE_INACTIVE')
    if subject != 'roof': errors.append('SUBJECT_NOT_IN_SCOPED_PACKAGE')
    return errors


def _scope_errors(rule, profile, module, depth, source, whitelist):
    scope = rule.get('scope', {})
    exact = profile['object_class']+'.'+profile['object_subclass']
    objects = scope.get('object_classes', [])
    generic_allowed = rule['rule_id'] in whitelist and profile['object_class'] in objects
    errors = []
    if exact not in objects and 'universal' not in objects and not generic_allowed: errors.append('OBJECT_SCOPE_MISMATCH')
    if module not in scope.get('modules', [])+scope.get('affects_modules', []): errors.append('MODULE_SCOPE_MISMATCH')
    if scope.get('functions') and not set(scope['functions']) & set(profile['active_functions']): errors.append('FUNCTION_SCOPE_INACTIVE')
    if scope.get('phases') and profile['project_phase'] not in scope['phases']: errors.append('PHASE_SCOPE_MISMATCH')
    if scope.get('stages') and profile['project_phase'] not in scope['stages']: errors.append('STAGE_SCOPE_UNRESOLVED')
    if scope.get('jurisdictions') and profile['jurisdiction'] not in scope['jurisdictions']: errors.append('JURISDICTION_SCOPE_MISMATCH')
    if module in scope.get('module_depth', {}):
        levels = source.data(MACHINE+'module_taxonomy.yaml')['modules'][module]['depth_levels']
        limits = scope['module_depth'][module]
        try:
            if not levels.index(limits['min']) <= levels.index(depth) <= levels.index(limits['max']):
                errors.append('DEPTH_SCOPE_MISMATCH')
        except (ValueError,KeyError): errors.append('DEPTH_SCOPE_UNRESOLVED')
    if any(scope.get(k) for k in ('applies_when','not_applicable_when','exclusions')):
        errors.append('RULE_CONDITIONS_REQUIRE_EXISTING_EVALUATOR')
    return errors


def _revision_errors(rule, passport, requirements):
    loc = rule.get('source_locator', {})
    errors = []
    if loc.get('document_code') != 'СП 17.13330.2017': errors.append('DOCUMENT_IDENTITY_NOT_BOUND')
    if requirements.get('requestedEditions', {}).get('roof', 'СП 17.13330.2017') != loc.get('document_code'):
        errors.append('REQUESTED_EDITION_NOT_BOUND')
    amendments = passport.get('amendments', [])
    if passport.get('status') != 'verified_current_revision_chain' or len(amendments) != 5:
        errors.append('SOURCE_REVISION_CHAIN_INCOMPLETE')
    if loc.get('edition_date') and loc['edition_date'] != '2017': errors.append('LOCATOR_EDITION_UNRESOLVED')
    if loc.get('amendment') and loc['amendment'] not in ('5','Изменение N 5'):
        errors.append('LOCATOR_AMENDMENT_UNRESOLVED')
    # The existing passport explicitly warns about changed table rows. Its
    # procedure is not an executable numeric Table4.1 row or amendment overlay.
    if loc.get('table'): errors.append('EXACT_CURRENT_TABLE_ROW_OVERLAY_NOT_BOUND')
    return errors


def map_legacy_evidence(normative, source_checks, source):
    """Retain PR66/67 bytes/statuses; only match identity, never promote trust."""
    roof = source.data(MACHINE+'evidence/sources_roofing_2026.yaml')['sources'][0]
    thermal = source.data(MACHINE+'evidence/source_sp50_2024_izhs.yaml')
    mappings = []
    for key, document in normative['registry']['documents'].items():
        matched = roof if document['edition']=='СП 17.13330.2017' else thermal if document['edition']=='СП 50.13330.2024' else None
        mappings.append({'legacyDocumentId':key,'machineSourceId':matched.get('source_id') if matched else None,
            'relation':'DOCUMENT_IDENTITY_ONLY' if matched else 'NOT_IN_ROOF_PACKAGE',
            'legacyMetadataVerification':document['metadataVerification'], 'acceptance':'NOT_VERIFIED'})
    return {'legacyNormativePackDigest':normative['normativePackDigest'],
        'legacySourceResultDigest':source_checks['resultDigest'], 'sourceMappings':mappings,
        'legacyBindings':copy.deepcopy(normative['bindings']), 'legacyChecks':copy.deepcopy(source_checks['checks']),
        'referencePolicy':MACHINE+'dependency_resolution_policy.yaml',
        'thermalReference':'EXACT_REFERENCE_OCCURRENCE_REQUIRED_NO_GLOBAL_PIN_OR_UPGRADE',
        'legacyDocumentPassIsNotMachineRulePass':True}


def integrate_existing_machine(normative, context, requirements, junctions, source_checks,
                               profile, module='architecture', subject='roof', source_root=SOURCE):
    source = ExistingMachineSource(source_root)
    if (normative.get('normativePackDigest') != RUN.digest({k:v for k,v in normative.items() if k!='normativePackDigest'}) or
            normative.get('nativeContextDigest') != RUN.digest(context) or
            normative.get('requirementsDigest') != RUN.digest(requirements) or
            normative.get('junctionInputDigest') != RUN.digest(junctions) or
            source_checks.get('resultDigest') != RUN.digest({k:v for k,v in source_checks.items() if k!='resultDigest'}) or
            source_checks.get('inputNormativePackDigest') != normative['normativePackDigest']):
        raise ValueError('MACHINE_INPUT_EVIDENCE_INVALIDATED')
    seen = set(); facts = []
    for j in junctions:
        if j['id'] in seen or j.get('family') != 'wall_roof': raise ValueError('MACHINE_WALL_ROOF_TARGET_REQUIRED')
        seen.add(j['id'])
        signature = BIND.native_binding_signature(context, j['guids'])
        matched = [r for r in normative['bindings'] if r['junctionId']==j['id']]
        if not matched or any(r['nativeContextSignature'] != signature for r in matched):
            raise ValueError('MACHINE_NATIVE_BINDING_INVALIDATED')
        elements = {e['guid'].lower():e for e in context['elements'].values()}
        types = []
        for g in j['guids']:
            e = elements[g.lower()]
            if e.get('kind') and e.get('type') and e['kind']!=e['type']:
                raise ValueError('MACHINE_NATIVE_TYPE_CONFLICT')
            types.append(e.get('kind') or e.get('type') or '')
        if sorted(types) != ['Roof','Wall']:
            raise ValueError('MACHINE_NATIVE_WALL_ROOF_REQUIRED')
        if any(not context.get('nativeGeometrySignatures',{}).get(g.lower()) for g in j['guids']):
            raise ValueError('MACHINE_NATIVE_BODY_EVIDENCE_REQUIRED')
        cse = requirements.get('cseFacts',{}).get(j['id'], {})
        cse_current = cse.get('nativeContextSignature')==signature and bool(cse.get('sourceEvidenceUri'))
        facts.append({'junctionId':j['id'], 'guids':j['guids'], 'nativeContextSignature':signature,
            'elements':[copy.deepcopy(elements[g.lower()]) for g in j['guids']],
            'bodySignatures':{g.lower():context['nativeGeometrySignatures'][g.lower()] for g in j['guids']},
            'cse':copy.deepcopy(cse) if cse_current else {}, 'cseEvidenceCurrent':cse_current,
            'cachedMetrics':copy.deepcopy(source_checks['nativeMetrics']), 'geometryRecomputed':False})
    errors = _profile_errors(profile, source, module, subject)
    result = {'schema':'APA_EXISTING_MACHINE_NORMATIVE_RESULTS_V1','projectId':normative['projectId'],
        'profile':copy.deepcopy(profile), 'profileErrors':errors, 'sourceCommit':COMMIT,
        'sourceLockDigest':RUN.digest(source.lock), 'legacy':map_legacy_evidence(normative,source_checks,source),
        'bimFacts':facts, 'bindings':[], 'nativeWriteCalls':0, 'nativeReadCalls':0, 'geometryRecomputed':False,
        'normativeAuthority':False, 'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED',
        'stagePack':[], 'nativeWritePlan':None, 'ruleEvaluator':'EXISTING_TDK_BLOCK_RESOLVER_AND_EVIDENCE_VALIDATOR'}
    if errors:
        result['status']='NOT_VERIFIED_PROFILE'
        result['bindings']=[{'junctionId':j['id'],'status':'NOT_VERIFIED','missingEvidence':errors} for j in junctions]
    else:
        exact = profile['object_class']+'.'+profile['object_subclass']
        index = source.data(MACHINE+'routes/index.yaml')
        if exact not in index['implemented_routes']:
            resolved,blocks,route = {'status':'ROUTE_MISSING','normative_authority':False},[],{}
        else:
            resolved,blocks,route = source.resolve(exact,module,profile['modules'][module],subject,{})
        result['runtimeResolution']=resolved
        result['status']='EXISTING_MACHINE_CONNECTED' if blocks else 'NOT_VERIFIED_ROUTE'
        if blocks:
            release = source.data(route['source_pack']['release_set'])
            whitelist = {rid for p in release['explicit_generic_rule_whitelist'] for rid in p['rule_ids']}
            aliases = source.data(MACHINE+'canonical_rule_aliases.yaml')['aliases']
            validator = source.module('scripts/validate_normative_evidence.py','apa_tdk_evidence_validator')
            canonical_seen = set()
            for block in blocks:
                ref = block['source_pack_ref']['primary_rule_file']
                ids = set(block['normative_closure']['rule_ids'])
                candidates = [r for r in source.data(ref)['rules'] if r['rule_id'] in ids]
                if {r['rule_id'] for r in candidates} != ids: raise ValueError('MACHINE_RULE_CLOSURE_MISSING')
                for rule in candidates:
                    rid = rule['rule_id']; canonical = aliases.get(rid, rid)
                    if canonical in canonical_seen: raise ValueError('MACHINE_DUPLICATE_RULE_CONFLICT')
                    canonical_seen.add(canonical)
                    scope = _scope_errors(rule,profile,module,profile['modules'][module],source,whitelist)
                    passport = source.data(MACHINE+'evidence/sources_roofing_2026.yaml')['sources'][0]
                    evidence = [e[2] for e in validator.validate_confirmed(rule,ref)]
                    if rule.get('status')!='confirmed': evidence.append('RULE_STATUS_NOT_CONFIRMED')
                    if rule['source_id'] != passport['source_id']: evidence.append('SOURCE_IDENTITY_NOT_BOUND')
                    revision = _revision_errors(rule,passport,requirements)
                    for fact in facts:
                        missing = scope+evidence+revision+['QUARANTINED_SOURCE_DESIGN_ONLY_RELEASE',
                            'UPSTREAM_ROOF_CALCULATOR_DECLARED_NOT_IMPLEMENTED']
                        if not fact['cseEvidenceCurrent']: missing.append('CSE_SOURCE_OR_NATIVE_SIGNATURE_NOT_BOUND')
                        result['bindings'].append({'junctionId':fact['junctionId'],'ruleId':canonical,'aliasUsed':rid if rid!=canonical else None,
                            'sourceRuleStatus':rule['status'],'sourceId':rule['source_id'],'sourceLocator':copy.deepcopy(rule['source_locator']),
                            'sourcePath':ref,'sourceBlob':source.lock['files'][ref]['gitBlob'],
                            'nativeContextSignature':fact['nativeContextSignature'], 'status':'NOT_VERIFIED',
                            'scopeGate':'MATCH' if not scope else 'DENY', 'evidenceGate':'STORED_FIELDS_PASS' if not evidence else 'DENY',
                            'revisionGate':'STORED_CHAIN_MATCH' if not revision else 'DENY',
                            'missingEvidence':missing,'engineeringApproved':False,'numericEvaluationExecuted':False})
        else:
            result['bindings']=[{'junctionId':j['id'],'status':'NOT_VERIFIED','missingEvidence':[resolved['status']]} for j in junctions]
    result['openedSourceFiles']=source.opened
    result['ruleFilesRead']=[p for p in source.opened if p.startswith(MACHINE+'rules/')]
    result['dependencyGraph']={'nodes':sorted({COMMIT,*seen,*[r.get('ruleId','profile') for r in result['bindings']]}),
        'edges':sorted([[r.get('ruleId','profile'),r['junctionId']] for r in result['bindings']]),
        'sceneWriterRequiredForAnyFutureWrite':True}
    result['resultDigest']=RUN.digest(result)
    return result


def attach_existing_machine(project_pack, result):
    if (project_pack.get('projectId')!=result.get('projectId') or
            project_pack.get('normativePackDigest')!=result['legacy']['legacyNormativePackDigest'] or
            result.get('resultDigest')!=RUN.digest({k:v for k,v in result.items() if k!='resultDigest'})):
        raise ValueError('MACHINE_RESULT_OR_PROJECT_PACK_INVALIDATED')
    out=copy.deepcopy(project_pack)
    out['existingMachineNormativeDigest']=result['resultDigest']
    out['existingMachineNormativeBindings']=copy.deepcopy(result['bindings'])
    out['normativeAuthority']=False
    return out
