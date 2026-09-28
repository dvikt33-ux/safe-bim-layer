"""Zero-setup startup model. No shell, git click, or model launcher."""
from __future__ import annotations

REQUIRED_STEPS = (
    'archicad-started',
    'ui-loaded',
    'bridge-started',
    'named-pipe-handshake',
    'sqlite-opened',
    'mailbox-checked',
    'ai-health',
    'ready',
)
FORBIDDEN_STEPS = ('powershell', 'manual-python', 'git-pull', 'github-desktop', 'ollama-manual')


def simulate_startup(*, auth_ok: bool, pipe_ok: bool = True, sqlite_ok: bool = True,
                     cloud_ok: bool = True, local_ok: bool = False) -> dict:
    steps = []
    steps.append('archicad-started')
    steps.append('ui-loaded')
    steps.append('bridge-started')
    if not pipe_ok:
        return {'steps': steps, 'local': 'ERROR', 'remote': 'OFFLINE', 'ready': False,
                'error': 'Named Pipe handshake не выполнен'}
    steps.append('named-pipe-handshake')
    if not sqlite_ok:
        return {'steps': steps, 'local': 'ERROR', 'remote': 'OFFLINE', 'ready': False,
                'error': 'локальная база не открылась'}
    steps.append('sqlite-opened')
    steps.append('mailbox-checked')
    steps.append('ai-health')
    steps.append('ready')
    remote = 'CONNECTED' if auth_ok else 'NEEDS_AUTH'
    ai = 'CONNECTED' if cloud_ok else ('CONNECTED' if local_ok else 'OFFLINE')
    return {
        'steps': steps,
        'local': 'READY',
        'remote': remote,
        'ai': ai,
        'ready': True,
        'forbidden': list(FORBIDDEN_STEPS),
        'error': '' if auth_ok else 'Нужна авторизация GitHub. Локальный Safe BIM работает.',
    }
