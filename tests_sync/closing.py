"""Close SQLite handles before the temporary directory is removed."""
import tempfile

from sync_bridge.remote_inbox import DurableRemoteInbox
from sync_bridge.store import BridgeStore


class ClosingDirectory:
    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._seen = {id(item) for item in BridgeStore.open_stores}
        self._seen.update(id(item) for item in DurableRemoteInbox.open_inboxes)
        return self._tmp.__enter__()

    def __exit__(self, exc_type, exc, tb):
        for item in list(BridgeStore.open_stores) + list(DurableRemoteInbox.open_inboxes):
            if id(item) not in self._seen:
                item.close()
        return self._tmp.__exit__(exc_type, exc, tb)
