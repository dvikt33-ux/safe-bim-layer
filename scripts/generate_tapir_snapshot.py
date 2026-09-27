"""Build an archicad-mcp Tapir snapshot from upstream schema JavaScript.

The generator reads the two documentation files shipped with a Tapir tag and
writes the same snapshot shape already pinned as tapir-1.5.8.json. It does not
contact Archicad and does not copy the Tapir repository into this tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _load_js_value(path: Path, prefix: str):
    text = path.read_text(encoding='utf-8')
    stripped = text.strip()
    if not stripped.startswith(prefix):
        raise SystemExit(f'{path} does not start with {prefix!r}')
    body = stripped[len(prefix):].strip()
    if body.endswith(';'):
        body = body[:-1]
    return json.loads(body), hashlib.sha256(path.read_bytes()).hexdigest()


def build_snapshot(source: Path, tag: str, commit: str) -> dict:
    groups, command_hash = _load_js_value(source / 'command_definitions.js', 'var gCommands =')
    common, common_hash = _load_js_value(source / 'common_schema_definitions.js', 'var gSchemaDefinitions =')
    commands = {}
    for group in groups:
        category = group['name']
        for command in group['commands']:
            name = command['name']
            if name in commands:
                raise SystemExit(f'duplicate Tapir command {name}')
            commands[name] = {
                'category': category,
                'description': command.get('description', ''),
                'version': command.get('version', ''),
                'parameters': command.get('inputScheme'),
                'returns': command.get('outputScheme'),
                'api': 'tapir',
                'name': name,
            }
    element_type = common.get('ElementType')
    if not isinstance(element_type, dict) or not isinstance(element_type.get('enum'), list):
        raise SystemExit('common schema has no ElementType enum')
    return {
        'commands': commands,
        'element_types': list(element_type['enum']),
        'common_schemas': common,
        '_metadata': {
            'format': 'archicad-mcp.tapir-snapshot/1',
            'provider': 'tapir',
            'provider_version': tag,
            'package_path': 'archicad_mcp/schemas/tapir.json',
            'upstream_repository': 'https://github.com/ENZYME-APD/tapir-archicad-automation',
            'upstream_tag': tag,
            'upstream_commit': commit,
            'license': 'MIT',
            'inputs': {
                'command_definitions.js': command_hash,
                'common_schema_definitions.js': common_hash,
            },
            'generator': 'scripts/generate_tapir_snapshot.py',
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot = build_snapshot(args.source, args.tag, args.commit)
    args.output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'commands={len(snapshot["commands"])} common={len(snapshot["common_schemas"])} -> {args.output}')


if __name__ == '__main__':
    main()
