"""Long-running zero-setup host for the verified Safe BIM Bridge stack.

This module composes existing S2.2-S2.4 components.  It does not widen the
Archicad command surface and it owns no BIM mutation path.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from bimexec.probes.backends import TapirBackend, _to_dict
from sync_bridge.archicad_context_provider import (
    ArchicadContextProvider,
    READ_COMMAND_ALLOWLIST,
)
from sync_bridge.bridge import InstanceConflict, LeaseLost, SafeBIMBridge
from sync_bridge.mailbox import GitHubContentsBackend, GitHubMailbox
from sync_bridge.pipe_win32 import NamedPipeUnavailable, production_transport
from sync_bridge.protocol import envelope
from sync_bridge.security import PeerIdentity
from sync_bridge.store import BridgeStore


HOST_STATUS = 'S2_5_RUNTIME_BOOTSTRAP_IMPLEMENTED_NOT_LIVE_VERIFIED'
DEFAULT_GITHUB_OWNER = 'dvikt33-ux'
DEFAULT_GITHUB_REPO = 'safe-bim-bridge'
DEFAULT_GITHUB_BRANCH = 'main'
DEFAULT_GITHUB_ROOT = 'safe-bim-mailbox'
DEFAULT_POLL_SECONDS = 2.0
DEFAULT_ARCHICAD_REFRESH_SECONDS = 3.0
DEFAULT_HEARTBEAT_SECONDS = 10.0


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class HostConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class HostConfig:
    data_dir: Path
    db_path: Path
    github_owner: str = DEFAULT_GITHUB_OWNER
    github_repo: str = DEFAULT_GITHUB_REPO
    github_branch: str = DEFAULT_GITHUB_BRANCH
    github_root: str = DEFAULT_GITHUB_ROOT
    archicad_port: int | None = None
    poll_seconds: float = DEFAULT_POLL_SECONDS
    archicad_refresh_seconds: float = DEFAULT_ARCHICAD_REFRESH_SECONDS
    heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS
    bridge_instance_id: str = 'bridge-1'

    @classmethod
    def from_environment(cls, env=None) -> 'HostConfig':
        env = os.environ if env is None else env
        raw_data = env.get('SAFE_BIM_DATA_DIR')
        if raw_data:
            data_dir = Path(raw_data).expanduser()
        elif env.get('LOCALAPPDATA'):
            data_dir = Path(env['LOCALAPPDATA']) / 'SafeBIM'
        else:
            data_dir = Path.home() / '.safe-bim'

        raw_db = env.get('SAFE_BIM_BRIDGE_DB')
        db_path = Path(raw_db).expanduser() if raw_db else data_dir / 'bridge.sqlite3'
        port = _optional_positive_int(env.get('SAFE_BIM_ARCHICAD_PORT'), 'SAFE_BIM_ARCHICAD_PORT')
        return cls(
            data_dir=data_dir,
            db_path=db_path,
            github_owner=_required_text(env.get('SAFE_BIM_GITHUB_OWNER', DEFAULT_GITHUB_OWNER), 'github owner'),
            github_repo=_required_text(env.get('SAFE_BIM_GITHUB_REPO', DEFAULT_GITHUB_REPO), 'github repo'),
            github_branch=_required_text(env.get('SAFE_BIM_GITHUB_BRANCH', DEFAULT_GITHUB_BRANCH), 'github branch'),
            github_root=_required_text(env.get('SAFE_BIM_GITHUB_ROOT', DEFAULT_GITHUB_ROOT), 'github root'),
            archicad_port=port,
            poll_seconds=_positive_float(env.get('SAFE_BIM_POLL_SECONDS', DEFAULT_POLL_SECONDS), 'poll seconds'),
            archicad_refresh_seconds=_positive_float(
                env.get('SAFE_BIM_ARCHICAD_REFRESH_SECONDS', DEFAULT_ARCHICAD_REFRESH_SECONDS),
                'Archicad refresh seconds'),
            heartbeat_seconds=_positive_float(
                env.get('SAFE_BIM_HEARTBEAT_SECONDS', DEFAULT_HEARTBEAT_SECONDS),
                'heartbeat seconds'),
            bridge_instance_id=_required_text(
                env.get('SAFE_BIM_BRIDGE_INSTANCE_ID', 'bridge-1'), 'bridge instance id'),
        )


class DefaultGitHubTokenProvider:
    """Resolve an existing GitHub login without asking for a manual token.

    Explicit process environment remains supported for automation.  Otherwise
    an already-authenticated GitHub CLI session is reused with ``gh auth token``.
    The token is kept only in this process memory and is never copied into the
    environment, SQLite, logs, or mailbox payloads.
    """

    def __init__(self, env=None, runner=None):
        self.env = os.environ if env is None else env
        self.runner = runner or subprocess.run
        self._cached: str | None = None
        self.source = 'none'

    def __call__(self) -> str | None:
        explicit = self.env.get('SAFE_BIM_GITHUB_TOKEN') or self.env.get('GITHUB_TOKEN')
        if explicit:
            self.source = 'environment'
            return explicit
        if self._cached:
            return self._cached

        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0
        try:
            completed = self.runner(
                ['gh', 'auth', 'token', '-h', 'github.com'],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5.0,
                check=False,
                creationflags=flags,
            )
        except (OSError, subprocess.SubprocessError):
            self.source = 'none'
            return None
        token = completed.stdout.strip() if completed.returncode == 0 and completed.stdout else ''
        if not token:
            self.source = 'none'
            return None
        self._cached = token
        self.source = 'gh-cli'
        return token


class TapirReadTransport:
    """Production adapter for the already verified S2.4 read-only provider."""

    def __init__(self, port: int | None = None, backend=None):
        self.backend = backend or TapirBackend(port=port)
        self.port = port

    def call(self, command: str, params: dict) -> dict:
        if command not in READ_COMMAND_ALLOWLIST:
            raise RuntimeError(f'Archicad read fence refused {command!r}')
        response = self.backend._tapir(command)(params or {})
        return _to_dict(response)

    def product_info(self) -> dict:
        """Best-effort official Archicad product metadata.

        Graphisoft's Python wrapper returns GetProductInfo as
        (version, buildNumber, languageCode). Product metadata is diagnostic:
        its absence must not make an otherwise healthy Archicad binding fail.
        """
        try:
            response = self.backend._official('GetProductInfo')()
        except Exception:
            return {}
        return _product_info_payload(response)

    def binding(self) -> dict:
        raw = self.call('GetProjectInfo', {})
        info = _addon_payload(raw)
        if not info:
            raise ConnectionError('Archicad GetProjectInfo returned no project identity')
        identity = {
            'projectPath': info.get('projectPath'),
            'projectLocation': info.get('projectLocation'),
            'projectName': info.get('projectName'),
            'isUntitled': info.get('isUntitled'),
            'isTeamwork': info.get('isTeamwork'),
        }
        packed = json.dumps(
            identity, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False
        ).encode('utf-8')
        product = self.product_info()
        instance = 'archicad-default' if self.port is None else f'archicad-{self.port}'
        return {
            'instanceId': instance,
            'logicalProjectId': 'live-local-' + hashlib.sha256(packed).hexdigest()[:20],
            'projectName': _optional_text(info.get('projectName')),
            'applicationVersion': _optional_text(
                product.get('version') or info.get('archicadVersion') or info.get('version')),
            'applicationBuild': _optional_text(
                product.get('buildNumber') or info.get('archicadBuild') or info.get('buildNumber')),
            'applicationLanguage': _optional_text(
                product.get('languageCode') or info.get('languageCode')),
        }


class BridgeHost:
    """Own the local pipe, persistent store, Bridge and read-only Archicad binding."""

    def __init__(self, config: HostConfig, *, identity: PeerIdentity | None = None,
                 token_provider=None, pipe_factory=production_transport,
                 transport=None, store_factory=BridgeStore, logger=None,
                 monotonic=time.monotonic, sleeper=time.sleep):
        self.config = config
        self.identity = identity
        self.token_provider = token_provider or DefaultGitHubTokenProvider()
        self.pipe_factory = pipe_factory
        self.transport = transport or TapirReadTransport(config.archicad_port)
        self.store_factory = store_factory
        self.log = logger or logging.getLogger('safe_bim_bridge_host')
        self.monotonic = monotonic
        self.sleeper = sleeper

        self.pipe = None
        self.store = None
        self.mailbox = None
        self.bridge = None
        self.context_provider = None
        self.current_binding: dict | None = None
        self.running = False
        self.stop_requested = False
        self._next_archicad_refresh = 0.0
        self._next_heartbeat = 0.0

    def start(self) -> dict:
        if self.running:
            return self.status()
        identity = self.identity or current_windows_identity()
        self.identity = identity
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.config.db_path.parent.mkdir(parents=True, exist_ok=True)

        store = self.store_factory(self.config.db_path)
        backend = GitHubContentsBackend(
            self.config.github_owner,
            self.config.github_repo,
            branch=self.config.github_branch,
            root=self.config.github_root,
            token_provider=self.token_provider,
        )
        mailbox = GitHubMailbox(backend=backend)
        provider = ArchicadContextProvider(
            self.transport,
            binding_reader=self.transport.binding,
        )
        bridge = SafeBIMBridge(
            store,
            mailbox,
            owner=identity,
            instance_id=self.config.bridge_instance_id,
            context_provider=provider,
        )

        pipe = None
        try:
            pipe = self.pipe_factory(identity.user_sid, identity.session_id)
            bridge.start()
        except BaseException:
            if pipe is not None:
                _close_quietly(pipe)
            _close_quietly(store)
            raise

        self.pipe = pipe
        self.store = store
        self.mailbox = mailbox
        self.context_provider = provider
        self.bridge = bridge
        self.running = True
        self.stop_requested = False
        now = self.monotonic()
        self._next_archicad_refresh = now
        self._next_heartbeat = now + self.config.heartbeat_seconds
        self.refresh_archicad()
        self.log.info('bridge host started; credential_source=%s',
                      getattr(self.token_provider, 'source', 'injected'))
        return self.status()

    def refresh_archicad(self) -> dict:
        self._require_running()
        assert self.bridge is not None and self.store is not None and self.identity is not None
        try:
            binding = self.transport.binding()
        except Exception as exc:
            if self.current_binding is not None:
                instance_id = self.current_binding.get('instanceId')
                existing = self.store.client(instance_id) if instance_id else None
                if (existing and existing.get('connection_state') == 'CONNECTED'
                        and int(existing.get('epoch') or -1) == self.bridge.epoch):
                    self.bridge.disconnect_archicad(instance_id)
            self.current_binding = None
            self.log.info('Archicad unavailable; error_type=%s', type(exc).__name__)
            return {'status': 'ARCHICAD_DISCONNECTED'}

        instance_id = _required_text(binding.get('instanceId'), 'Archicad instanceId')
        project_id = _required_text(binding.get('logicalProjectId'), 'Archicad logicalProjectId')

        previous_instance = self.current_binding.get('instanceId') if self.current_binding else None
        if previous_instance and previous_instance != instance_id:
            previous = self.store.client(previous_instance)
            if (previous and previous.get('connection_state') == 'CONNECTED'
                    and int(previous.get('epoch') or -1) == self.bridge.epoch):
                self.bridge.disconnect_archicad(previous_instance)

        existing = self.store.client(instance_id)
        connected_here = bool(
            existing
            and existing.get('connection_state') == 'CONNECTED'
            and int(existing.get('epoch') or -1) == self.bridge.epoch
        )
        if connected_here and existing.get('logical_project_id') == project_id:
            self.store.upsert_client(
                instance_id, self.identity.session_id, project_id, _utc_now(),
                'CONNECTED', self.bridge.epoch)
        else:
            if connected_here:
                self.bridge.disconnect_archicad(instance_id)
            hello = envelope(
                'HELLO', {'logicalProjectId': project_id}, instance_id=instance_id)
            self.bridge.handshake(hello.to_dict(), self.identity)

        self.current_binding = dict(binding)
        return {
            'status': 'ARCHICAD_CONNECTED',
            'instanceId': instance_id,
            'logicalProjectId': project_id,
        }

    def step(self) -> dict:
        self._require_running()
        assert self.bridge is not None
        now = self.monotonic()
        archicad = None
        if now >= self._next_archicad_refresh:
            archicad = self.refresh_archicad()
            self._next_archicad_refresh = now + self.config.archicad_refresh_seconds
        if now >= self._next_heartbeat:
            self.bridge.heartbeat()
            self._next_heartbeat = now + self.config.heartbeat_seconds
        remote = self.bridge.tick()
        if remote.get('status') == 'LEASE_LOST':
            raise LeaseLost('LEASE_LOST')
        return {'archicad': archicad, 'remote': remote, 'status': self.status()}

    def run_forever(self) -> None:
        self.start()
        try:
            while not self.stop_requested:
                self.step()
                if not self.stop_requested:
                    self.sleeper(self.config.poll_seconds)
        finally:
            self.close()

    def request_stop(self) -> None:
        self.stop_requested = True

    def status(self) -> dict:
        health = self.bridge.health() if self.bridge is not None and self.bridge.running else None
        return {
            'hostStatus': HOST_STATUS,
            'running': self.running,
            'dbPath': str(self.config.db_path),
            'pipeOpen': bool(self.pipe is not None and getattr(self.pipe, 'handle', None) is not None),
            'credentialSource': getattr(self.token_provider, 'source', 'injected'),
            'archicad': dict(self.current_binding) if self.current_binding else None,
            'bridge': health,
        }

    def close(self) -> None:
        if self.bridge is not None:
            try:
                if self.bridge.running:
                    self.bridge.stop()
            finally:
                _close_quietly(self.store)
        else:
            _close_quietly(self.store)
        _close_quietly(self.pipe)
        self.running = False
        self.pipe = None
        self.store = None
        self.mailbox = None
        self.bridge = None
        self.context_provider = None
        self.current_binding = None

    def _require_running(self) -> None:
        if not self.running or self.bridge is None:
            raise RuntimeError('bridge host is stopped')


def current_windows_identity() -> PeerIdentity:
    if os.name != 'nt':
        raise HostConfigurationError('Safe BIM Bridge host requires Windows')
    return PeerIdentity(_windows_user_sid(), _windows_session_id())


def _windows_user_sid() -> str:
    advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    TOKEN_QUERY = 0x0008
    TOKEN_USER_CLASS = 1

    advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                         ctypes.POINTER(wintypes.HANDLE)]
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_uint,
                                             ctypes.c_void_p, wintypes.DWORD,
                                             ctypes.POINTER(wintypes.DWORD)]
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p,
                                                ctypes.POINTER(wintypes.LPWSTR)]
    advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        needed = wintypes.DWORD(0)
        advapi32.GetTokenInformation(token, TOKEN_USER_CLASS, None, 0, ctypes.byref(needed))
        if needed.value == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi32.GetTokenInformation(
                token, TOKEN_USER_CLASS, buffer, needed.value, ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())

        class SID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [('Sid', ctypes.c_void_p), ('Attributes', wintypes.DWORD)]

        class TOKEN_USER(ctypes.Structure):
            _fields_ = [('User', SID_AND_ATTRIBUTES)]

        token_user = ctypes.cast(buffer, ctypes.POINTER(TOKEN_USER)).contents
        string_sid = wintypes.LPWSTR()
        if not advapi32.ConvertSidToStringSidW(token_user.User.Sid, ctypes.byref(string_sid)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            sid = string_sid.value
            if not sid or not sid.startswith('S-1-'):
                raise HostConfigurationError('Windows returned an invalid user SID')
            return sid
        finally:
            kernel32.LocalFree(ctypes.cast(string_sid, ctypes.c_void_p))
    finally:
        kernel32.CloseHandle(token)


def _windows_session_id() -> str:
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel32.ProcessIdToSessionId.restype = wintypes.BOOL
    session = wintypes.DWORD(0)
    if not kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(session)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str(session.value)


def configure_logging(data_dir: Path) -> logging.Logger:
    data_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('safe_bim_bridge_host')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(
            data_dir / 'bridge-host.log', maxBytes=512 * 1024, backupCount=2, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(handler)
    return logger


def main() -> int:
    try:
        config = HostConfig.from_environment()
        host = BridgeHost(config, logger=configure_logging(config.data_dir))
        host.run_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    except (HostConfigurationError, InstanceConflict, NamedPipeUnavailable, LeaseLost) as exc:
        try:
            config = locals().get('config')
            if config is not None:
                configure_logging(config.data_dir).error('bridge host failed; error_type=%s', type(exc).__name__)
        except Exception:
            pass
        return 2


def _addon_payload(response: dict) -> dict:
    result = response.get('result') if isinstance(response, dict) else None
    if isinstance(result, dict) and isinstance(result.get('addOnCommandResponse'), dict):
        return result['addOnCommandResponse']
    return response if isinstance(response, dict) else {}


def _product_info_payload(response) -> dict:
    if isinstance(response, (tuple, list)) and len(response) >= 3:
        return {
            'version': response[0],
            'buildNumber': response[1],
            'languageCode': response[2],
        }

    data = _to_dict(response)
    if isinstance(data, dict) and data:
        return {
            'version': data.get('version') or data.get('archicadVersion'),
            'buildNumber': data.get('buildNumber') or data.get('build'),
            'languageCode': data.get('languageCode') or data.get('language'),
        }

    return {
        'version': getattr(response, 'version', None),
        'buildNumber': getattr(response, 'buildNumber', None),
        'languageCode': getattr(response, 'languageCode', None),
    }


def _required_text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HostConfigurationError(f'{label} is required')
    return value.strip()


def _optional_text(value) -> str | None:
    if value in (None, ''):
        return None
    return str(value)


def _positive_float(value, label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise HostConfigurationError(f'{label} must be positive') from exc
    if parsed <= 0:
        raise HostConfigurationError(f'{label} must be positive')
    return parsed


def _optional_positive_int(value, label: str) -> int | None:
    if value in (None, ''):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise HostConfigurationError(f'{label} must be a positive integer') from exc
    if parsed <= 0:
        raise HostConfigurationError(f'{label} must be a positive integer')
    return parsed


def _close_quietly(value) -> None:
    if value is None:
        return
    close = getattr(value, 'close', None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


if __name__ == '__main__':
    raise SystemExit(main())
