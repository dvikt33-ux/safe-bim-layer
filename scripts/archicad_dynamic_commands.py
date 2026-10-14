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
        rows['API.'+name]=dict(name='API.'+name,api='official-json',provider='Archicad.JSON',version='29',category='Official JSON API',description=inspect.getdoc(method) or '',parameters=params,
            returns=dict(type='object',required=sorted(keys),properties={k:{} for k in keys},description='Result keys from installed official SDK; nested output constraints remain SDK typed, not a full JSON schema.'),
            outputSchemaCoverage='SDK_RESULT_KEYS_ONLY',inputValidation='INSTALLED_OFFICIAL_TYPED_CONSTRUCTOR',availability='DOCUMENTED_PRODUCT_MATCH_COMMAND_NOT_PROBED')
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

    def register_availability(self,command,available):
        if command not in self.catalog['commands'] or type(available) is not bool:raise ValueError('INVALID_REGISTRATION_EVIDENCE')
        self.registration[command]=available

    def select(self,command):
        row=copy.deepcopy(self.catalog['commands'][command]);row.update(effect=effect(command),status='LIVE_VERIFIED' if command in self.live else 'BLOCKED' if self.registration.get(command) is False else 'ROUTABLE',runtimeRegistered=self.registration.get(command),catalogHash=self.fingerprint)
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
        ticket=dict(schema='APA_DYNAMIC_CALL_V1',command=command,parameters=parameters,catalogHash=self.fingerprint,effect=effect(command),nativeWritePermission=False)
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
        if not authorization or impact not in {'READ_ONLY','MODEL','PROJECT','ATTRIBUTES','DOCUMENTATION','EXTERNAL'}:raise ValueError('EXPLICIT_IMPACT_AND_AUTHORIZATION_REQUIRED')
        affected=sorted(g.lower() for g in affected);retained=sorted(g.lower() for g in retained)
        if set(affected)&set(retained):raise ValueError('AFFECTED_AND_RETAINED_SCOPE_OVERLAP')
        def target_ids(v):
            if isinstance(v,dict):
                if 'elementId' in v and isinstance(v['elementId'],dict) and 'guid' in v['elementId']:yield v['elementId']['guid'].lower()
                for item in v.values():yield from target_ids(item)
            elif isinstance(v,list):
                for item in v:yield from target_ids(item)
        if impact=='MODEL' and ticket['effect'] in {'MODIFY','DELETE'} and not set(target_ids(ticket['parameters']))<=set(affected):raise ValueError('DYNAMIC_ELEMENT_TARGET_OUTSIDE_AUTHORIZED_SCOPE')
        value=dict(schema='APA_DYNAMIC_OPERATION_V1',ticket=ticket,binding=binding,affectedGuids=affected,retainedGuids=retained,authorizationRef=authorization,impact=impact)
        value['hash']=self.A.RUN.digest(value);return value

    def qualify_scope(self,scope,command,parameters,source_hash):
        self.validate(scope['ticket'])
        if self.registration.get(command) is False:raise ValueError('COMMAND_NOT_REGISTERED_IN_RUNTIME')
        if scope['hash']!=self.A.RUN.digest({k:v for k,v in scope.items() if k!='hash'}) or scope['ticket']['command']!=command or scope['ticket']['parameters']!=parameters or scope['ticket']['hash']!=source_hash or not scope.get('authorizationRef'):raise ValueError('DYNAMIC_OPERATION_SCOPE_DRIFT')

    def read(self,api,ticket,reviewed_read_only=False):
        self.validate(ticket)
        if not reviewed_read_only or ticket['effect']!='READ_CANDIDATE':raise ValueError('READ_ONLY_EFFECT_REVIEW_REQUIRED')
        api.bind_dynamic_commands(self)
        with api.dynamic_call(ticket):result=api(ticket['command'],ticket['parameters'])
        self.validate_result(ticket['command'],result);self.live[ticket['command']]=dict(kind='READ_SCHEMA_PASS',resultHash=self.A.RUN.digest(result))
        return result

    def execute(self,writer,scene_id,ticket,affected,retained_signatures,saved_sha256,authorization,impact,verify_after):
        """Delegate exactly one approved intent to the existing SceneWriter."""
        import hashlib
        import archicad_bim_documentation as D
        import archicad_connected_components as C
        self.validate(ticket);writer.api.bind_dynamic_commands(self)
        binding=writer.guarded_binding();scope=self.scope(ticket,binding,affected,retained_signatures,authorization,impact)
        pre=dict(sourcePlanHash=ticket['hash'],binding=binding,integrationBindings=dict(dependencies=dict(dynamicOperation=scope)))
        def preserved():
            model=D.capture_full_model(writer.api,retained_signatures)
            if C.retained_geometry_signatures(model,list(retained_signatures))!=retained_signatures:raise ValueError('DYNAMIC_RETAINED_MODEL_CHANGED')
        def before():
            if self.catalog.get('_metadata',{}).get('binding',{}).get('apaRuntimeIdentity'):
                self.A.verify_native_runtime_identity(writer.api,self.catalog)
            if writer.api('GetAddOnVersion',{}).get('version')!=CONTRACTS.source_version(self.catalog):raise ValueError('DYNAMIC_PROVIDER_VERSION_DRIFT')
            if hashlib.sha256(Path(binding['path']).read_bytes()).hexdigest()!=saved_sha256:raise ValueError('DYNAMIC_SAVED_FILE_CHANGED')
            current=set(self.A.inventory_guids(writer.api))
            if current!=set(scope['affectedGuids'])|set(scope['retainedGuids']):raise ValueError('DYNAMIC_COMPLETE_INVENTORY_SCOPE_REQUIRED')
            preserved();return dict(status='DYNAMIC_BASELINE_PASS')
        def after(reply,prior):
            self.validate_result(ticket['command'],reply)
            proof=verify_after(reply,prior)
            if not isinstance(proof,dict) or not str(proof.get('status','')).endswith('PASS'):raise ValueError('DYNAMIC_INDEPENDENT_READBACK_REQUIRED')
            preserved();return proof
        intent=dict(sceneId=scene_id,sourcePlanHash=ticket['hash'],command=ticket['command'],parameters=ticket['parameters'],target=binding)
        result=writer.execute_bound_operation(pre,scene_id,ticket['command'],ticket['parameters'],self.A.RUN.digest(intent),before,after)
        if result['status']=='PASS':self.live[ticket['command']]=dict(kind='JOURNALED_NATIVE_READBACK_PASS',sceneId=scene_id)
        return result
