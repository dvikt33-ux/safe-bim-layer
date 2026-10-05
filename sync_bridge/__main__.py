"""Quiet production entry for the long-running Safe BIM Bridge host."""
from __future__ import annotations

from sync_bridge.write_bridge import install_write_bridge

# Keep the existing host composition intact and replace only its bridge class.
install_write_bridge()

from sync_bridge.host import main


if __name__ == '__main__':
    raise SystemExit(main())
