"""Schema catalog adapter for the existing BIM Graph, KG and SceneWriter.

Discovery and preparation never authorize a project write. Unknown effects
remain explicit. No transport, search implementation or journal is added.
"""
from __future__ import annotations
import ast
import copy
import inspect
import json
import textwrap
import typing
import hashlib
from pathlib import Path
import archicad_batch_contracts as CONTRACTS

def effect(name):
    name=name.removeprefix('API.')
    for prefix,kind in [('Create','CREATE'),('Clone','CREATE'),('Modify','MODIFY'),('Set','MODIFY'),('Delete','DELETE'),('Remove','DELETE'),('Get','READ_CANDIDATE'),('Is','READ_CANDIDATE')]:
        if name.startswith(prefix):return kind
    return 'UNKNOWN_OR_PROJECT_STATE'

def _type_schema(t,seen=()):
    if t in (str,int,float,bool):return {'type':{str:'string',int:'integer',float:'number',bool:'boolean'}[t]}
    origin=typing.get_origin(t);args=typing.get_args(t)
    if origin is list:return dict(type='array',items=_type_schema(args[0],seen))
    if args:return {'anyOf':[{'type':'null'} if a is type(None) else _type_schema(a,seen) for a in args]}
    alternatives=getattr(getattr(t,'constructor',None),'optional_types',None)
    if alternatives:return {'anyOf':[_type_schema(a,seen) for a in alternatives]}
    if inspect.isclass(t) and hasattr(t,'get_classinfo') and t not in seen:
        info=t.get_classinfo();props={k:_type_schema(v,(*seen,t)) for k,v in info.fields.items()}
        for key,validators in info.value_validators.items():
            for validator in validators:
                for cell in validator.__closure__ or ():
                    values=cell.cell_contents
                    if isinstance(values,(list,set,tuple)) and all(type(v) in (str,int,float,bool) for v in values):props[key]['enum']=list(values)
        signature=inspect.signature(t)
        required=[k for k,p in signature.parameters.items() if p.default is p.empty and k in props]
        return dict(type='object',properties=props,required=required,additionalProperties=False)
    if getattr(t,'__name__','')=='UUID':return dict(type='string',format='uuid')
    return {'description':'Official SDK type '+str(t)}

def official_catalog(commands):
    """Use installed official SDK contracts; never call commands for discovery.

    Nested parameter constructors are extracted from the trusted installed
    SDK source. Only the class and its metadata registrations are evaluated;
    the function body containing network dispatch is never evaluated.
    """
    import importlib
    module=importlib.import_module(type(commands).__module__);rows={};constructors={}
    for name,method in inspect.getmembers(type(commands),inspect.isfunction):
        if name.startswith('_'):continue
        source=textwrap.dedent(inspect.getsource(method));tree=ast.parse(source);fn=tree.body[0]
        selected=[];param_class=None
        for node in fn.body:
            if isinstance(node,ast.ClassDef) and node.name.endswith('_parameters'):
                selected.append(node);param_class=node.name
            elif param_class and isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and ast.unparse(node.value).startswith(param_class+'.get_classinfo()'):
                selected.append(node)
        if selected:
            ns=dict(vars(module));exec(compile(ast.Module(body=selected,type_ignores=[]),'<installed-archicad-sdk-contract>','exec'),ns)
            constructor=ns[param_class];params=_type_schema(constructor);constructors['API.'+name]=constructor
        else:params=dict(type='object',maxProperties=0);constructors['API.'+name]=None
        keys=set()
        for node in ast.walk(fn):
            if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Subscript) and ast.unparse(node.value)=="result['result']" and isinstance(node.slice,ast.Constant) and isinstance(node.slice.value,str):keys.add(node.slice.value)
        properties={k:{} for k in keys};builders={}
        for node in ast.walk(fn):
            if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='_ListBuilder' and node.value.args and isinstance(node.value.args[0],ast.Name):
                for target in node.targets:
                    if isinstance(target,ast.Name):builders[target.id]=getattr(module,node.value.args[0].id,None)
        for node in ast.walk(fn):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in builders and node.args:
                item=node.args[0]
                if isinstance(item,ast.Subscript) and isinstance(item.slice,ast.Constant) and item.slice.value in properties:
                    properties[item.slice.value]=dict(type='array',items=_type_schema(builders[node.func.id]))
        rows['API.'+name]=dict(name='API.'+name,api='official-json',provider='Archicad.JSON',version='29',category='Official JSON API',description=inspect.getdoc(method) or '',parameters=params,
            returns=dict(type='object',required=sorted(keys),properties=properties),
            outputSchemaCoverage='SDK_TYPED_ARRAYS_AND_RESULT_KEYS',inputValidation='INSTALLED_OFFICIAL_TYPED_CONSTRUCTOR',implementationSHA256=hashlib.sha256(source.encode()).hexdigest(),availability='DOCUMENTED_PRODUCT_MATCH_COMMAND_NOT_PROBED')
    return rows,constructors

class DynamicCommands:
    def __init__(self,catalog,official=None):
        import archicad_project_accelerator as A
        self.A=A;self.catalog=copy.deepcopy(catalog);self.constructors={}
        self.catalog['commands']={k:dict(v,provider=v.get('provider','TapirCommand'),availability=v.get('availability','LIVE_EXPORT_REGISTERED'),outputSchemaCoverage=v.get('outputSchemaCoverage','FULL_PROVIDER_SCHEMA')) for k,v in self.catalog['commands'].items()}
        if official is not None:
            rows,self.constructors=official_catalog(official);self.catalog['commands'].update(rows)
        self.fingerprint=A.RUN.digest(self.catalog)
        self.live={};self.registration={}
        self.policies={};self.callable={}

    def review_policy(self,command,kind,impact,evidence):
        """Effect is reviewed metadata, never a permission inferred from a name."""
        if command not in self.catalog['commands'] or kind not in {'READ_ONLY','CREATE','MODIFY','DELETE','TRANSACTION','SERVICE','UNKNOWN'} or impact not in {'READ_ONLY','MODEL','PROJECT','ATTRIBUTES','DOCUMENTATION','EXTERNAL'} or not isinstance(evidence,dict) or not evidence.get('source') or not evidence.get('sha256'):raise ValueError('SOURCE_BACKED_OPERATION_POLICY_REQUIRED')
        self.policies[command]=dict(kind=kind,impact=impact,evidence=copy.deepcopy(evidence))

    def load_policies(self,manifest):
        """Explicit version/hash-bound operator metadata, not name inference."""
        if manifest.get('catalogHash')!=self.fingerprint:raise ValueError('OPERATION_MANIFEST_CATALOG_DRIFT')
        for name,policy in manifest['operations'].items():
            self.review_policy(name,policy['kind'],policy['impact'],policy['evidence'])
        return dict(reviewed=len(self.policies),unknown=sum(p['kind']=='UNKNOWN' for p in self.policies.values()))

    def operation_kind(self,command):
        return self.policies.get(command,{}).get('kind','UNKNOWN')

    def add_provider(self,namespace,contracts,source,common_schemas=None):
        if not namespace or '.' in namespace or not source:raise ValueError('PROVIDER_NAMESPACE_AND_SOURCE_REQUIRED')
        common_schemas=common_schemas or {}
        def refs(value):
            if isinstance(value,dict):return {k:('#/'+namespace+'__'+v[2:] if k=='$ref' and isinstance(v,str) and v.startswith('#/') and v[2:] in common_schemas else refs(v)) for k,v in value.items()}
            if isinstance(value,list):return [refs(v) for v in value]
            return value
        for name,value in common_schemas.items():self.catalog['common_schemas'][namespace+'__'+name]=refs(value)
        for name,row in contracts.items():
            if '.' in name:raise ValueError('PROVIDER_COMMAND_NAME_INVALID')
            key='AddOn.'+namespace+'.'+name
            if key in self.catalog['commands']:raise ValueError('PROVIDER_COMMAND_DUPLICATE')
            self.catalog['commands'][key]=dict(refs(copy.deepcopy(row)),name=key,provider=namespace,namespace=namespace,commandName=name,api='addon-json',availability='SOURCE_CONTRACT_NOT_RUNTIME_PROBED',source=source)
        self.fingerprint=self.A.RUN.digest(self.catalog)

    def include_source_snapshot(self,snapshot,label):
        """Keep absent candidate contracts discoverable without claiming loaded."""
        prefix=label+'__';definitions=snapshot['common_schemas']
        def rewrite(v):
            if isinstance(v,dict):return {k:('#/'+prefix+x[2:] if k=='$ref' and isinstance(x,str) and x.startswith('#/') and x[2:] in definitions else rewrite(x)) for k,x in v.items()}
            if isinstance(v,list):return [rewrite(x) for x in v]
            return v
        missing={k:v for k,v in snapshot['commands'].items() if k not in self.catalog['commands']}
        if missing:
            for name,value in definitions.items():self.catalog['common_schemas'][prefix+name]=rewrite(value)
            for name,row in missing.items():self.catalog['commands'][name]=dict(rewrite(copy.deepcopy(row)),sourceSnapshot=label,availability='SOURCE_SNAPSHOT_NOT_RUNTIME_PROBED')
            self.fingerprint=self.A.RUN.digest(self.catalog)
        return sorted(missing)

    def register_availability(self,command,available):
        if command not in self.catalog['commands'] or type(available) is not bool:raise ValueError('INVALID_REGISTRATION_EVIDENCE')
        self.registration[command]=available

    def select(self,command):
        row=copy.deepcopy(self.catalog['commands'][command]);row.update(effect=self.operation_kind(command),policy=copy.deepcopy(self.policies.get(command)),status='LIVE_VERIFIED' if command in self.live else 'CALLABLE_VERIFIED' if command in self.callable else 'BLOCKED' if self.registration.get(command) is False else 'SCHEMA_VALID',catalogDiscovered=True,routable=True,runtimeRegistered=self.registration.get(command),catalogHash=self.fingerprint)
        return row

    def index(self,markdown,db):
        """Reuse the unchanged Knowledge Graph section index, with summaries only."""
        from archicad_knowledge_access import components
        text=['# APA registered command catalog']
        for name,row in sorted(self.catalog['commands'].items()):
            text.extend(['## '+name,row['category']+' / '+effect(name)+' / '+row.get('description','')[:700]])
        Path(markdown).write_text('\n\n'.join(text),encoding='utf8')
        return components()['sections'].build([Path(markdown)],Path(db))

    def search(self,db,query,limit=5):
        from archicad_knowledge_access import components
        return components()['sections'].search(Path(db),query,limit=min(limit,10),max_snippet=220)

    def prepare(self,command,parameters):
        if self.A.RUN.digest(self.catalog)!=self.fingerprint:raise ValueError('CATALOG_CONTENT_DRIFT')
        if command not in self.catalog['commands']:raise ValueError('COMMAND_NOT_DISCOVERED')
        # Serialization rejects NaN and makes the immutable intent independent
        # of the caller's subsequently mutated dictionary.
        parameters=json.loads(self.A.RUN.canonical(parameters))
        if not isinstance(parameters,dict):raise ValueError('COMMAND_PARAMETERS_OBJECT_REQUIRED')
        CONTRACTS._validator(self.catalog,command).validate(parameters)
        if command in self.constructors and self.constructors[command] is not None:
            value=self.constructors[command](**parameters)
            if not value.get_classinfo().is_valid_instance(value):raise ValueError('OFFICIAL_SDK_INSTANCE_CONSTRAINT_FAILED')
        ticket=dict(schema='APA_DYNAMIC_CALL_V1',command=command,parameters=parameters,catalogHash=self.fingerprint,effect=self.operation_kind(command),policyHash=self.A.RUN.digest(self.policies.get(command)),nativeWritePermission=False)
        ticket['hash']=self.A.RUN.digest(ticket)
        return ticket

    def validate(self,ticket):
        expected=self.prepare(ticket['command'],ticket['parameters'])
        if ticket!=expected:raise ValueError('DYNAMIC_CALL_SCHEMA_OR_TICKET_DRIFT')
        return ticket

    def validate_result(self,command,result):
        row=self.catalog['commands'][command]
        doc=copy.deepcopy(self.catalog);doc['commands'][command]['parameters']=row.get('returns') or dict(type='object')
        CONTRACTS._validator(doc,command).validate(result)
        def errors(v):
            if isinstance(v,dict):return 'error' in v or v.get('success') is False or any(errors(x) for x in v.values())
            if isinstance(v,list):return any(errors(x) for x in v)
            return False
        if errors(result):raise ValueError('NATIVE_RESULT_CONTAINS_FAILURE')
        return result

    def scope(self,ticket,binding,affected,retained,authorization,impact):
        self.validate(ticket)
        if ticket['effect']=='UNKNOWN':raise ValueError('EXECUTION_REQUIRES_SOURCE_REVIEWED_OPERATION_EFFECT')
        if self.policies[ticket['command']]['impact']!=impact:raise ValueError('OPERATION_POLICY_IMPACT_MISMATCH')
        if not authorization or impact not in {'READ_ONLY','MODEL','PROJECT','ATTRIBUTES','DOCUMENTATION','EXTERNAL'}:raise ValueError('EXPLICIT_IMPACT_AND_AUTHORIZATION_REQUIRED')
        affected=sorted(g.lower() for g in affected);retained=sorted(g.lower() for g in retained)
        if set(affected)&set(retained):raise ValueError('AFFECTED_AND_RETAINED_SCOPE_OVERLAP')
        def target_ids(v):
            if isinstance(v,dict):
                if 'elementId' in v and isinstance(v['elementId'],dict) and 'guid' in v['elementId']:yield v['elementId']['guid'].lower()
                for item in v.values():yield from target_ids(item)
            elif isinstance(v,list):
                for item in v:yield from target_ids(item)
        if impact=='MODEL' and ticket['effect'] not in {'READ_ONLY','CREATE'} and not set(target_ids(ticket['parameters']))<=set(affected):raise ValueError('DYNAMIC_ELEMENT_TARGET_OUTSIDE_AUTHORIZED_SCOPE')
        value=dict(schema='APA_DYNAMIC_OPERATION_V1',ticket=ticket,binding=binding,affectedGuids=affected,retainedGuids=retained,authorizationRef=authorization,impact=impact)
        value['hash']=self.A.RUN.digest(value);return value

    def qualify_scope(self,scope,command,parameters,source_hash):
        self.validate(scope['ticket'])
        if self.registration.get(command) is False:raise ValueError('COMMAND_NOT_REGISTERED_IN_RUNTIME')
        if scope['hash']!=self.A.RUN.digest({k:v for k,v in scope.items() if k!='hash'}) or scope['ticket']['command']!=command or scope['ticket']['parameters']!=parameters or scope['ticket']['hash']!=source_hash or not scope.get('authorizationRef'):raise ValueError('DYNAMIC_OPERATION_SCOPE_DRIFT')

    def read(self,api,ticket,reviewed_read_only=False):
        self.validate(ticket)
        if not reviewed_read_only or ticket['effect']!='READ_ONLY':raise ValueError('SOURCE_REVIEWED_READ_ONLY_EFFECT_REQUIRED')
        self.A.RUN.guarded_project(api)
        self.probe_runtime(api,ticket['command'])
        api.bind_dynamic_commands(self)
        with api.dynamic_call(ticket):result=api(ticket['command'],ticket['parameters'])
        self.validate_result(ticket['command'],result);self.callable[ticket['command']]=dict(kind='READ_SCHEMA_PASS',resultHash=self.A.RUN.digest(result))
        return result

    def probe_runtime(self,api,command):
        """Reacquire registration for each selected add-on command before call."""
        row=self.catalog['commands'][command]
        if command.startswith('API.'):
            product=api('API.GetProductInfo',{})
            if product.get('version')!=29:raise ValueError('OFFICIAL_API_PRODUCT_VERSION_DRIFT')
            return dict(status='CLIENT_PRODUCT_MATCH_NOT_PER_METHOD_REGISTRATION')
        namespace=row.get('namespace',row.get('provider','TapirCommand'));name=row.get('commandName',command)
        api.allowed|={'API.IsAddOnCommandAvailable'}
        available=api('API.IsAddOnCommandAvailable',dict(addOnCommandId=dict(commandNamespace=namespace,commandName=name)))
        self.register_availability(command,available.get('available'))
        if not self.registration[command]:raise ValueError('COMMAND_NOT_REGISTERED_IN_CURRENT_RUNTIME')
        return dict(status='RUNTIME_AVAILABLE',namespace=namespace,command=name)

    def _schema_at(self,schema,pointer):
        for token in pointer.strip('/').split('/') if pointer else []:
            while '$ref' in schema:
                ref=schema['$ref']
                if not ref.startswith('#/'):raise ValueError('EXTERNAL_SCHEMA_REFERENCE_NOT_PINNED')
                schema=self.catalog['common_schemas'][ref[2:]]
            token=token.replace('~1','/').replace('~0','~')
            if schema.get('type')=='array':
                if not token.isdigit():raise ValueError('RESULT_POINTER_ARRAY_INDEX_REQUIRED')
                schema=schema['items']
            else:schema=schema.get('properties',{})[token]
        return schema

    def _schema_example(self,schema):
        while '$ref' in schema:
            ref=schema['$ref']
            if not ref.startswith('#/'):raise ValueError('EXTERNAL_SCHEMA_REFERENCE_NOT_PINNED')
            schema=self.catalog['common_schemas'][ref[2:]]
        if 'const' in schema:return schema['const']
        if schema.get('enum'):return schema['enum'][0]
        for key in ('anyOf','oneOf'):
            if key in schema:return self._schema_example(next(s for s in schema[key] if s.get('type')!='null'))
        kind=schema.get('type')
        if kind=='object':return {k:self._schema_example(v) for k,v in schema.get('properties',{}).items() if k in schema.get('required',[])}
        if kind=='array':return [self._schema_example(schema.get('items',{})) for _ in range(max(1,schema.get('minItems',0)))]
        if kind=='string':return '00000000-0000-4000-8000-000000000000' if schema.get('format')=='uuid' else 'schema-placeholder'
        if kind=='boolean':return False
        if kind in {'integer','number'}:return max(1,schema.get('minimum',0),schema.get('exclusiveMinimum',0)+1)
        raise ValueError('RESULT_REFERENCE_REQUIRES_A_TYPED_SOURCE_SCHEMA')

    @staticmethod
    def _result_at(value,pointer):
        if pointer and not pointer.startswith('/'):raise ValueError('RESULT_JSON_POINTER_MUST_BE_ABSOLUTE')
        for token in pointer.strip('/').split('/') if pointer else []:
            token=token.replace('~1','/').replace('~0','~')
            value=value[int(token)] if isinstance(value,list) else value[token]
        return copy.deepcopy(value)

    def prepare_workflow(self,graph):
        """Result bindings extend the existing graph compiler, not its scheduler."""
        if not isinstance(graph,dict) or set(graph)!={'operations'}:raise ValueError('EXISTING_BIM_GRAPH_FORMAT_REQUIRED')
        by_id={s['id']:s for s in graph['operations']};bindings={}
        def placeholders(value,dependencies):
            if isinstance(value,dict) and '$result' in value:
                ref=value['$result']
                if set(value)!={'$result'} or set(ref)!={'step','pointer'} or ref['step'] not in by_id:raise ValueError('INVALID_RESULT_DEPENDENCY')
                dependencies.append(ref['step'])
                source=self.catalog['commands'][by_id[ref['step']]['command']].get('returns')
                return self._schema_example(self._schema_at(source,ref['pointer']))
            if isinstance(value,dict):return {k:placeholders(v,dependencies) for k,v in value.items()}
            if isinstance(value,list):return [placeholders(v,dependencies) for v in value]
            return value
        template=copy.deepcopy(graph)
        for step in template['operations']:
            dependencies=list(step.get('after',[]));step['params']=placeholders(step['params'],dependencies);step['after']=list(dict.fromkeys(dependencies))
            bindings[step['id']]=step['after'];self.prepare(step['command'],step['params'])
        checked=self.A.SCENE.GRAPH.compile_graph(self.catalog,template,runtime_version=CONTRACTS.source_version(self.catalog))
        if checked['status']!='PLAN_VALIDATED_OFFLINE':raise ValueError('BIM_GRAPH_DEPENDENCY_OR_SCHEMA_INVALID:'+str(checked))
        return dict(schema='APA_DYNAMIC_BIM_WORKFLOW_V1',graph=copy.deepcopy(graph),catalogHash=self.fingerprint,policyHash=self.A.RUN.digest(self.policies),sourcePlanHash=self.A.RUN.digest(graph),templatePlanHash=checked['sourcePlanHash'],executionOrder=checked['executionOrder'],dependencies=bindings,executionPermission=False)

    def run_workflow(self,api,plan,writer=None,scopes=None):
        """Sequential graph reuse; each mutation uses the same writer/SQLite.

        No failed step is retried. External result bindings are resolved and
        revalidated against the concrete consumer contract before dispatch.
        """
        if self.prepare_workflow(plan['graph'])!=plan:raise ValueError('DYNAMIC_WORKFLOW_PLAN_DRIFT')
        steps={s['id']:s for s in plan['graph']['operations']};results={};trace=[]
        def resolve(value):
            if isinstance(value,dict) and '$result' in value:
                ref=value['$result'];return self._result_at(results[ref['step']],ref['pointer'])
            if isinstance(value,dict):return {k:resolve(v) for k,v in value.items()}
            if isinstance(value,list):return [resolve(v) for v in value]
            return value
        for sid in plan['executionOrder']:
            step=steps[sid];ticket=self.prepare(step['command'],resolve(step['params']))
            if ticket['effect']=='READ_ONLY':reply=self.read(api,ticket,reviewed_read_only=True)
            else:
                if writer is None or sid not in (scopes or {}):raise ValueError('WORKFLOW_MUTATION_REQUIRES_EXACT_STEP_SCOPE')
                scope=scopes[sid]
                outcome=self.execute(writer,scope['scene_id'],ticket,scope['affected'],scope['retained_signatures'],scope['saved_sha256'],scope['authorization'],scope['impact'],scope['verify_after'],verify_before=scope.get('verify_before'))
                if outcome['status']!='PASS':return dict(status='STOPPED_UNKNOWN_OUTCOME',stoppedAt=sid,outcome=outcome,completedSteps=trace,automaticRetry=False)
                reply=outcome['nativeResponse']
            results[sid]=reply;trace.append(dict(id=sid,command=step['command'],resultHash=self.A.RUN.digest(reply),status='CALLABLE_VERIFIED'))
        return dict(status='WORKFLOW_CALLABLE_VERIFIED',sourcePlanHash=plan['sourcePlanHash'],trace=trace,results=results,automaticRetry=False)

    def native_facts(self,workflow,model_step,elements_step,boxes_step=None):
        """Reuse existing BREP/IFC quantities; provider boxes remain separate."""
        import archicad_connected_components as C
        from archicad_connected_ifc import native_body_quantities
        results=workflow['results'];model=C.G.normalize_dump(results[model_step]);native={e['guid'].lower():e for e in model['elements']}
        selected=results[elements_step]['elements'];boxes=results[boxes_step]['boundingBoxes3D'] if boxes_step else None
        if boxes is not None and len(boxes)!=len(selected):raise ValueError('GEOMETRY_RESULT_GUID_CARDINALITY_MISMATCH')
        rows=[]
        for index,item in enumerate(selected):
            guid=item['elementId']['guid'].lower();element=native[guid]
            vertices=[v for body in element.get('bodies',[]) for v in body['vertices']]
            bounds={axis+suffix:operation(v[i] for v in vertices) for i,axis in enumerate('xyz') for suffix,operation in [('Min',min),('Max',max)]} if vertices else None
            provider=boxes[index]['boundingBox3D'] if boxes else None
            delta=max(abs(bounds[k]-provider[k]) for k in bounds) if bounds and provider else None
            rows.append(dict(guid=guid,type=element['type'],homeStory=element['homeStory'],materials=element.get('materialBindings',{}),relationships=element.get('relationships',{}),bounds=bounds,geometryAuthority='ACTUAL_RESULTANT_NATIVE_BREP' if bounds else 'NATIVE_BODY_NOT_AVAILABLE',quantities=native_body_quantities(element),providerBounds=provider,providerBoundsDelta=delta,providerBoundsInterpretation='MATCH' if delta is not None and delta<1e-5 else 'DIFFERS_NOT_PHYSICAL_BODY_AUTHORITY' if delta is not None else 'NOT_QUERIED'))
        return dict(schema='APA_SHARED_NATIVE_FACTS_V1',sourcePlanHash=workflow['sourcePlanHash'],elements=rows,engineering='NOT_VERIFIED')

    def execute(self,writer,scene_id,ticket,affected,retained_signatures,saved_sha256,authorization,impact,verify_after,verify_before=None):
        """Delegate exactly one approved intent to the existing SceneWriter."""
        import hashlib
        import archicad_bim_documentation as D
        import archicad_connected_components as C
        self.validate(ticket);writer.api.bind_dynamic_commands(self)
        self.probe_runtime(writer.api,ticket['command'])
        binding=writer.guarded_binding();scope=self.scope(ticket,binding,affected,retained_signatures,authorization,impact)
        pre=dict(sourcePlanHash=ticket['hash'],binding=binding,integrationBindings=dict(dependencies=dict(dynamicOperation=scope)))
        def preserved():
            model=D.capture_full_model(writer.api,retained_signatures)
            if C.retained_geometry_signatures(model,list(retained_signatures))!=retained_signatures:raise ValueError('DYNAMIC_RETAINED_MODEL_CHANGED')
        def before():
            if ticket['effect']!='READ_ONLY' and not (ticket['command']=='SaveProject' and ticket['parameters']=={}) and not callable(verify_before):raise ValueError('OPERATION_SPECIFIC_PREFLIGHT_REQUIRED')
            if self.catalog.get('_metadata',{}).get('binding',{}).get('apaRuntimeIdentity'):
                self.A.verify_native_runtime_identity(writer.api,self.catalog)
            if writer.api('GetAddOnVersion',{}).get('version')!=CONTRACTS.source_version(self.catalog):raise ValueError('DYNAMIC_PROVIDER_VERSION_DRIFT')
            if hashlib.sha256(Path(binding['path']).read_bytes()).hexdigest()!=saved_sha256:raise ValueError('DYNAMIC_SAVED_FILE_CHANGED')
            current=set(self.A.inventory_guids(writer.api))
            if current!=set(scope['affectedGuids'])|set(scope['retainedGuids']):raise ValueError('DYNAMIC_COMPLETE_INVENTORY_SCOPE_REQUIRED')
            preserved()
            if verify_before is not None:
                proof=verify_before(writer.api)
                if not isinstance(proof,dict) or not str(proof.get('status','')).endswith('PASS'):raise ValueError('OPERATION_SPECIFIC_PREFLIGHT_NOT_VERIFIED')
            return dict(status='DYNAMIC_BASELINE_PASS')
        def after(reply,prior):
            self.validate_result(ticket['command'],reply)
            proof=verify_after(reply,prior)
            if not isinstance(proof,dict) or not str(proof.get('status','')).endswith('PASS'):raise ValueError('DYNAMIC_INDEPENDENT_READBACK_REQUIRED')
            preserved();return proof
        intent=dict(sceneId=scene_id,sourcePlanHash=ticket['hash'],command=ticket['command'],parameters=ticket['parameters'],target=binding)
        result=writer.execute_bound_operation(pre,scene_id,ticket['command'],ticket['parameters'],self.A.RUN.digest(intent),before,after)
        if result['status']=='PASS':self.live[ticket['command']]=dict(kind='JOURNALED_NATIVE_READBACK_PASS',sceneId=scene_id)
        return result
