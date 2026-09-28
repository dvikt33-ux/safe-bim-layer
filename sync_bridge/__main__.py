"""Quiet production entry for the long-running Safe BIM Bridge host."""
from __future__ import annotations

from sync_bridge.host import main


if __name__ == '__main__':
    raise SystemExit(main())
