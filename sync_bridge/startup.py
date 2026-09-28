"""Zero-setup startup model. No shell, git click, or model launcher."""
from __future__ import annotations

REQUIRED_STEPS = (
    'ui-loaded',
    'bridge-started',
    'named-pipe-listening',
    'sqlite-opened',
    'mailbox-checked',
    'ai-health',
    'ready',
)
FORBIDDEN_STEPS = ('powershell', 'manual-python', 'git-pull', 'github-desktop', 'ollama-manual')


def status_board(*, local_ready: bool, auth_ok: bool, ai: str, archicad_connected: bool) -> dict:
    """Independent channel facts. Missing GitHub auth is not a local ERROR."""
    return {
        'LOCAL': 'LOCAL_READY' if local_ready else 'LOCAL_ERROR',
        'REMOTE': 'REMOTE_CONNECTED' if auth_ok else 'REMOTE_NEEDS_AUTH',
        'AI': ai,
        'ARCHICAD': 'ARCHICAD_CONNECTED' if archicad_connected else 'ARCHICAD_DISCONNECTED',
    }


def simulate_startup(*, auth_ok: bool, pipe_ok: bool = True, sqlite_ok: bool = True,
                     cloud_ok: bool = True, local_ok: bool = False, archicad_ok: bool = False) -> dict:
    """Local bridge readiness does not require a connected Archicad client."""
    steps = []
    steps.append('ui-loaded')
    steps.append('bridge-started')
    if not pipe_ok:
        board = status_board(local_ready=False, auth_ok=auth_ok, ai='AI_OFFLINE', archicad_connected=False)
        return {'steps': steps, 'local': board['LOCAL'], 'remote': board['REMOTE'], 'ai': board['AI'],
                'archicad': board['ARCHICAD'], 'board': board, 'ready': False,
                'error': 'Named Pipe не слушает'}
    steps.append('named-pipe-listening')
    steps.append('archicad-handshake' if archicad_ok else 'archicad-not-required')
    if not sqlite_ok:
        board = status_board(local_ready=False, auth_ok=auth_ok, ai='AI_OFFLINE', archicad_connected=archicad_ok)
        return {'steps': steps, 'local': board['LOCAL'], 'remote': board['REMOTE'], 'ai': board['AI'],
                'archicad': board['ARCHICAD'], 'board': board, 'ready': False,
                'error': 'локальная база не открылась'}
    steps.append('sqlite-opened')
    steps.append('mailbox-checked')
    steps.append('ai-health')
    steps.append('ready')
    if cloud_ok or local_ok:
        ai = 'AI_CONNECTED'
    else:
        ai = 'AI_OFFLINE'
    board = status_board(local_ready=True, auth_ok=auth_ok, ai=ai, archicad_connected=archicad_ok)
    return {
        'steps': steps,
        'local': board['LOCAL'],
        'remote': board['REMOTE'],
        'ai': board['AI'],
        'archicad': board['ARCHICAD'],
        'board': board,
        'ready': True,
        'forbidden': list(FORBIDDEN_STEPS),
        'error': '' if auth_ok else 'Нужна авторизация GitHub. Локальный Safe BIM работает.',
    }
