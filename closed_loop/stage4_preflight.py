"""Identity-first read-only gate for the explicitly named Stage 4 environment."""
import argparse
import json
import ntpath
import os
from pathlib import Path
import urllib.request
from .live_wall import ROOT, read
from .wall_attempts import durable_json

IMPLEMENTATION_FILES = ('closed_loop/models.py','closed_loop/orchestrator.py','closed_loop/wall_attempts.py',
    'closed_loop/live_wall.py','closed_loop/live_wall_hardening.py','closed_loop/stage4_fixture.py','closed_loop/stage4_preflight.py','closed_loop/stage4_live_scenario.py',
    'scripts/stage4_audit_pack.py','scripts/archicad_executor.py','scripts/archicad_chat_executor.py',
    'scripts/archicad_write_cycles/wall_joint_cycle.py','archicad-addon/Examples/model_dump_v1.py')


TARGET_PROJECT_ENV = 'SAFE_BIM_STAGE4_PROJECT_PATH'

def _normalize_project_path(value):
    return ntpath.normcase(ntpath.normpath(str(value).strip()))

def _project_binding(identity):
    explicit = os.environ.get(TARGET_PROJECT_ENV)
    if explicit:
        if not ntpath.isabs(explicit):
            raise ValueError(f'{TARGET_PROJECT_ENV} must be an absolute Windows path')
        actual = identity.get('projectPath')
        if not actual or _normalize_project_path(actual) != _normalize_project_path(explicit):
            raise ValueError('WRONG_PROJECT: explicit Stage 4 project path does not match active PLN')
        return {'mode':'EXPLICIT_STAGE4_PATH','expectedProjectPath':explicit}
    baseline = read(ROOT / 'outputs/closed-loop-stage1/preflight.json')['identity']
    if identity != baseline:
        raise ValueError('WRONG_PROJECT: stop before follow-on commands')
    return {'mode':'STAGE1_BASELINE_IDENTITY','expectedProjectPath':baseline.get('projectPath')}

def preflight(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    def call(command, addon=True):
        payload = {'command': 'API.ExecuteAddOnCommand', 'parameters': {
            'addOnCommandId': {'commandNamespace': 'TapirCommand', 'commandName': command},
            'addOnCommandParameters': {}}} if addon else {'command': command}
        stem = command.replace('.', '-')
        durable_json(output / (stem + '.request.json'), payload)
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:19723', json.dumps(payload).encode(),
                {'Content-Type': 'application/json'}), timeout=15) as response:
            raw = response.read()
        (output / (stem + '.response.json')).write_bytes(raw)
        envelope = json.loads(raw)
        if envelope.get('succeeded') is not True:
            raise ValueError('Preflight transport failed: '+command)
        return envelope['result'].get('addOnCommandResponse', envelope['result'])
    report = {'status': 'BLOCKED', 'mutationAttempted': False}
    try:
        identity = call('GetProjectInfo')
        binding = _project_binding(identity)
        product, tapir = call('API.GetProductInfo', False), call('GetAddOnVersion')
        if (product.get('version'), product.get('buildNumber'), product.get('languageCode')) != (29, 3000, 'RUS'):
            raise ValueError('Unsupported Archicad environment')
        expected_tapir = read(ROOT / 'outputs/closed-loop-stage1/preflight.json')['tapir']
        if tapir != expected_tapir:
            raise ValueError('Tapir differs from the proven 1.5.10 baseline')
        report.update(status='PASS', identity=identity, projectBinding=binding, archicad=product, tapir=tapir, endpoint='127.0.0.1:19723')
    except Exception as exc:
        report['reason'] = f'{type(exc).__name__}: {exc}'
    durable_json(output / 'preflight.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = preflight(parser.parse_args().output)
    print(json.dumps(result, ensure_ascii=True))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
