"""Existing B3 factory + existing semantic registration + accepted group contracts.

Returns the original DynamicCommands instance. No new dispatcher or executor,
no dependencies installed, and no native commands called during attachment.
"""
import argparse
import importlib.util
import json
import hashlib
from pathlib import Path

ROOT=Path(r'C:\LocalAI\APA_AC29_Stable')


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def native_command_router(schema_path=None,official_commands=None,include_functional_modules=False):
    factory=load(ROOT/'external-tools/apa-ifc-geometry-b3/apa_ifc_geometry_factory_b3.py','apa_existing_b3_combined')
    router=factory.native_command_router(schema_path,official_commands,include_functional_modules)
    # The existing B3 chain verifies and attaches V1+V2+B1+B2+C1+B3 itself.
    prefix='AddOn.APASemantic.'
    existing={k for k in router.catalog['commands'] if k.startswith(prefix)}
    if existing:raise ValueError('INSTALLED_COMBINED_SEMANTIC_ALREADY_ATTACHED_UNEXPECTED')
    semantic=load(ROOT/'external-tools/apa-semantic-v1/apa_semantic_catalog.py','apa_existing_semantic_combined')
    semantic.register(router)
    from apa_ac29_installed_group_provider import attach
    attach(router)
    import apa_dxf_source_preflight as dxf
    data=Path(dxf.__file__).read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(data).hexdigest()!='8f8cca6e17c1d3032d61fdb8401678d2adbb71a1f986258ed5f94bf2c776fbc9':
        raise ValueError('INSTALLED_DXF_PREFLIGHT_SOURCE_DRIFT')
    dxf.register(router)
    return router


def inventory(router):
    local=sorted(k for k,v in router.catalog['commands'].items() if v.get('api')=='local-python')
    semantic=[k for k in local if k.startswith('AddOn.APASemantic.')]
    # Optional original APAAnalysis commands are distinct from these 34 reads.
    extra=[k for k in local if k.startswith('AddOn.APADXFPreflight.')]
    files=[k for k in local if not k.startswith(('AddOn.APASemantic.','AddOn.APAAnalysis.','AddOn.APADXFPreflight.'))]
    if len(files)!=30 or len(semantic)!=4 or any(router.operation_kind(k)!='READ_ONLY' for k in files+semantic+extra):
        raise ValueError('INSTALLED_THIRTY_FILE_AND_FOUR_SEMANTIC_READS_REQUIRED')
    return dict(catalogCommands=len(router.catalog['commands']),fileCommands=files,
                semanticCommands=semantic,additionalFileCommands=extra,nativeWrites=0,automaticNativeExecution=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--task-json',type=Path)
    args=p.parse_args()
    router=native_command_router();result=inventory(router)
    if args.task_json:
        import archicad_project_accelerator as A
        result['preview']=A.prepare_auto_optimized_native_task(router,json.loads(args.task_json.read_text(encoding='utf8')))
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
