"""Quiet production entry. Does not open a console and does not call Archicad."""
from __future__ import annotations

import os
import sys

from sync_bridge.pipe_win32 import NamedPipeUnavailable, production_transport


def main() -> int:
    if os.name != 'nt':
        sys.stderr.write('SafeBIMBridge: Windows Named Pipe required; HTTP fallback is disabled\n')
        return 2
    try:
        production_transport(os.environ.get('SAFE_BIM_USER_SID', ''), os.environ.get('SAFE_BIM_SESSION', ''))
    except (NamedPipeUnavailable, ValueError) as exc:
        sys.stderr.write(f'SafeBIMBridge: {exc}\n')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
