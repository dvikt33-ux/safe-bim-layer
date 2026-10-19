"""Two accepted SDK contracts on the existing Router; no native execution."""
import hashlib
import json
from pathlib import Path

CONTRACT_SHA = '638409b9fcbc8d009b8b149bb3975f34de08cee592b0c4394fe49e245dc984b2'


def contract():
    p=Path(__file__).resolve().parents[1]/'schemas/accelerator/installed-group-copy.json'
    data=p.read_bytes()
    if hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()!=CONTRACT_SHA:
        raise ValueError('INSTALLED_GROUP_CODE_OWNED_CONTRACT_DRIFT')
    return json.loads(data)


def attach(router):
    spec=contract();missing={}
    for name,row in spec['commands'].items():
        key='AddOn.TapirCommand.'+name
        if key not in router.catalog['commands']:
            missing[name]=row
        else:
            current=router.catalog['commands'][key]
            if any(current.get(k)!=row.get(k) for k in ('parameters','returns','version','implementationSHA256')):
                raise ValueError('INSTALLED_GROUP_EXISTING_CONTRACT_DRIFT:'+key)
    if missing:router.add_provider('TapirCommand',missing,'NativeGroupCommands.inc')
    for name,row in spec['commands'].items():
        key='AddOn.TapirCommand.'+name
        router.catalog['commands'][key]['implementationSHA256']=row['implementationSHA256']
        kind='CREATE' if name=='CloneNativeGroupV1' else 'READ_ONLY'
        router.review_policy(key,kind,'MODEL' if kind=='CREATE' else 'READ_ONLY',
            dict(source='PR179 accepted existing native group contract; runtime/scopes remain required',sha256=row['implementationSHA256']))
    router.fingerprint=router.A.RUN.digest(router.catalog)
    return dict(sourceContracts=2,runtimeRegistration='NOT_PROBED',executionPermission=False)


def verify_runtime(api):
    actual=api('GetAPARuntimeInfoV1',{})
    if actual!=contract()['acceptedRuntime']:
        raise ValueError('INSTALLED_GROUP_UNACCEPTED_NATIVE_RUNTIME_BUILD')
    return actual
