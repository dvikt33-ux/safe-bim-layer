"""Minimal GitHub mailbox -> Tapir write path.

This module deliberately layers on top of the existing read-only bridge instead
of changing its context-capture state machine.  It is the smallest closed loop
needed for ChatGPT-authored JOB objects to reach the already-loaded Tapir add-on
and return verified RESULT objects.

Safety properties of this first write skeleton:
- exact command allowlist; unknown commands fail closed;
- one queued JOB is executed per bridge tick;
- instance/project binding is checked immediately before and after the call;
- write timeouts are UNKNOWN_OUTCOME and are never retried automatically;
- a process that dies with a RUNNING job converts it to UNKNOWN_OUTCOME on start;
- write commands get read-back through GetDetailsOfElements and
  Get3DBoundingBoxes whenever affected GUIDs are known.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from bimexec.probes.backends import _to_dict
from sync_bridge.bridge import SafeBIMBridge


WRITE_COMMAND_ALLOWLIST = frozenset({
    'CreateBeams',
    'CreateWalls',
    'CreateSlabs',
    'ModifySlabs',
    'CreateRoofs',
    'CreateMorphs',
    'DeleteElements',
})

READ_COMMAND_ALLOWLIST = frozenset({
    'GetElementsByType',
    'GetDetailsOfElements',
    'Get3DBoundingBoxes',
})

JOB_COMMAND_ALLOWLIST = WRITE_COMMAND_ALLOWLIST | READ_COMMAND_ALLOWLIST


class JobValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required_text(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JobValidationError('INVALID_JOB', field + ' required')
    return value


def _payload(response):
    """Return Tapir addOnCommandResponse when present, otherwise the object itself."""
    if not isinstance(response, dict):
        return {}
    result = response.get('result')
    if isinstance(result, dict) and isinstance(result.get('addOnCommandResponse'), dict):
        return result['addOnCommandResponse']
    return response


def _guid_from_row(row):
    if not isinstance(row, dict):
        return None
    element = row.get('elementId')
    guid = element.get('guid') if isinstance(element, dict) else None
    return guid if isinstance(guid, str) and guid else None


def _affected_guids(command: str, params: dict, raw_result: dict) -> list[str]:
    guids: list[str] = []
    seen = set()

    def add(value):
        if isinstance(value, str) and value and value.casefold() not in seen:
            seen.add(value.casefold())
            guids.append(value)

    if command.startswith('Create'):
        for row in _payload(raw_result).get('elements', []):
            add(_guid_from_row(row))
    elif command == 'ModifySlabs':
        for row in params.get('slabsWithDetails', []):
            add(_guid_from_row(row))
    elif command == 'DeleteElements':
        for row in params.get('elements', []):
            add(_guid_from_row(row))
    return guids


class TapirJobExecutor:
    """Execute one allowlisted Tapir operation against the host's bound backend."""

    def __init__(self, transport):
        self.transport = transport

    def validate(self, body: dict) -> dict:
        if not isinstance(body, dict):
            raise JobValidationError('INVALID_JOB', 'JOB payload must be an object')
        command = _required_text(body.get('command'), 'command')
        request_id = _required_text(body.get('requestId'), 'requestId')
        instance_id = _required_text(body.get('instanceId'), 'instanceId')
        project_id = _required_text(body.get('logicalProjectId'), 'logicalProjectId')
        params = body.get('params', {})
        if not isinstance(params, dict):
            raise JobValidationError('INVALID_JOB', 'params must be an object')
        if command not in JOB_COMMAND_ALLOWLIST:
            raise JobValidationError('UNSUPPORTED_COMMAND', command)
        return {
            'command': command,
            'requestId': request_id,
            'instanceId': instance_id,
            'logicalProjectId': project_id,
            'params': deepcopy(params),
        }

    def execute(self, body: dict) -> dict:
        try:
            job = self.validate(body)
        except JobValidationError as exc:
            return self._failure(body, exc.code, str(exc))

        command = job['command']
        try:
            self._require_binding(job['instanceId'], job['logicalProjectId'])
            raw = self._call(command, job['params'])
            guids = _affected_guids(command, job['params'], raw)
            verification = self._read_back(command, guids)
            self._require_binding(job['instanceId'], job['logicalProjectId'])
            return {
                'status': 'SUCCESS',
                'success': True,
                'requestId': job['requestId'],
                'instanceId': job['instanceId'],
                'logicalProjectId': job['logicalProjectId'],
                'command': command,
                'affectedElementGuids': guids,
                'rawResult': raw,
                'verification': verification,
                'completedAt': _now(),
            }
        except TimeoutError:
            return {
                'status': 'UNKNOWN_OUTCOME',
                'success': False,
                'requestId': job['requestId'],
                'instanceId': job['instanceId'],
                'logicalProjectId': job['logicalProjectId'],
                'command': command,
                'error': {'code': 'TIMEOUT', 'message': 'write outcome is unknown; automatic retry forbidden'},
                'completedAt': _now(),
            }
        except JobValidationError as exc:
            return self._failure(job, exc.code, str(exc))
        except Exception as exc:
            return self._failure(job, type(exc).__name__, str(exc))

    def _call(self, command: str, params: dict) -> dict:
        # Production TapirReadTransport exposes the already-connected TapirBackend.
        # Using it directly keeps the existing read fence intact for context capture.
        backend = getattr(self.transport, 'backend', None)
        if backend is not None and callable(getattr(backend, '_tapir', None)):
            response = backend._tapir(command)(deepcopy(params or {}))
            return _to_dict(response)

        # Test/injected transports may expose a generic execute/call_any/call method.
        for name in ('execute', 'call_any', 'call'):
            fn = getattr(self.transport, name, None)
            if callable(fn):
                response = fn(command, deepcopy(params or {}))
                return _to_dict(response)
        raise ConnectionError('no Tapir transport available')

    def _binding(self) -> dict:
        reader = getattr(self.transport, 'binding', None)
        if not callable(reader):
            raise JobValidationError('ARCHICAD_NOT_AVAILABLE', 'transport has no binding()')
        value = reader()
        if not isinstance(value, dict):
            raise JobValidationError('ARCHICAD_NOT_AVAILABLE', 'binding is unavailable')
        return value

    def _require_binding(self, instance_id: str, project_id: str) -> None:
        binding = self._binding()
        if binding.get('instanceId') != instance_id:
            raise JobValidationError('INSTANCE_MISMATCH', 'bound Archicad instance changed')
        if binding.get('logicalProjectId') != project_id:
            raise JobValidationError('PROJECT_MISMATCH', 'bound Archicad project changed')

    def _read_back(self, command: str, guids: list[str]) -> dict:
        if command in READ_COMMAND_ALLOWLIST:
            return {'mode': 'COMMAND_RESULT'}
        if not guids:
            return {'mode': 'NO_GUIDS', 'details': None, 'boundingBoxes3D': None}
        elements = [{'elementId': {'guid': guid}} for guid in guids]
        details = self._call('GetDetailsOfElements', {'elements': elements})
        boxes = self._call('Get3DBoundingBoxes', {'elements': elements})
        return {
            'mode': 'GUID_READBACK',
            'details': details,
            'boundingBoxes3D': boxes,
        }

    @staticmethod
    def _failure(body: dict, code: str, message: str) -> dict:
        body = body if isinstance(body, dict) else {}
        return {
            'status': 'FAILED',
            'success': False,
            'requestId': body.get('requestId'),
            'instanceId': body.get('instanceId'),
            'logicalProjectId': body.get('logicalProjectId'),
            'command': body.get('command'),
            'error': {'code': code, 'message': message},
            'completedAt': _now(),
        }


class WriteSafeBIMBridge(SafeBIMBridge):
    """Existing SafeBIMBridge plus one-at-a-time mailbox JOB execution."""

    def __init__(self, *args, job_executor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if job_executor is None:
            provider = kwargs.get('context_provider')
            reads = getattr(provider, '_reads', None)
            transport = getattr(reads, '_transport', None)
            job_executor = TapirJobExecutor(transport) if transport is not None else None
        self.job_executor = job_executor

    def start(self) -> dict:
        result = super().start()
        self._recover_inflight_jobs()
        return self.health() if isinstance(result, dict) else result

    def health(self) -> dict:
        result = super().health()
        result['archicadWriteApi'] = self.job_executor is not None
        result['archicadWriteCommands'] = sorted(JOB_COMMAND_ALLOWLIST)
        result['writeExecutionPolicy'] = 'ONE_JOB_PER_TICK_NO_TIMEOUT_RETRY'
        return result

    def tick(self) -> dict:
        polled = super().tick()
        if polled.get('status') == 'LEASE_LOST':
            return polled
        execution = self.process_next_job()
        if execution is not None:
            polled['execution'] = execution
            # super().tick() already flushed the older outbox; publish the fresh RESULT now.
            try:
                more = self.flush_outbox()
            except Exception as exc:
                more = [{'status': 'RESULT_FLUSH_ERROR', 'error': type(exc).__name__}]
            polled.setdefault('published', []).extend(more)
        return polled

    def process_next_job(self):
        self._require_owner()
        queued = [job for job in self.store.jobs() if job.get('state') == 'QUEUED']
        if not queued:
            return None
        job = queued[0]
        job_id = job['job_id']
        source_message_id = job.get('source_message_id')
        self._set_job_state(job_id, 'RUNNING')
        if source_message_id:
            self.store.set_message_state(source_message_id, 'PROCESSING')

        if self.job_executor is None:
            body = job.get('payload') if isinstance(job.get('payload'), dict) else {}
            result = TapirJobExecutor._failure(
                body, 'ARCHICAD_WRITE_UNAVAILABLE', 'no local Tapir job executor is configured')
        else:
            try:
                result = self.job_executor.execute(job.get('payload'))
            except BaseException as exc:
                body = job.get('payload') if isinstance(job.get('payload'), dict) else {}
                result = TapirJobExecutor._failure(body, type(exc).__name__, str(exc))

        result['jobId'] = job_id
        result['sourceMessageId'] = source_message_id
        final_state = result.get('status')
        if final_state not in {'SUCCESS', 'FAILED', 'UNKNOWN_OUTCOME'}:
            final_state = 'FAILED'
        self.queue_result(job_id, result)
        self._set_job_state(job_id, final_state)
        if source_message_id:
            self.store.set_message_state(source_message_id, 'PROCESSED')
        return {
            'jobId': job_id,
            'status': final_state,
            'command': result.get('command'),
            'requestId': result.get('requestId'),
        }

    def _set_job_state(self, job_id: str, state: str) -> None:
        # BridgeStore predates remote execution and has no public state mutator yet.
        # Keep this compatibility shim local to the feature rather than migrating schema.
        self.store._db.execute('UPDATE remote_jobs SET state=? WHERE job_id=?', (state, job_id))

    def _recover_inflight_jobs(self) -> None:
        for job in self.store.jobs():
            if job.get('state') != 'RUNNING':
                continue
            job_id = job['job_id']
            if self.store.result(job_id) is None:
                body = job.get('payload') if isinstance(job.get('payload'), dict) else {}
                result = TapirJobExecutor._failure(
                    body,
                    'BRIDGE_RESTART_DURING_WRITE',
                    'previous process stopped while write was in flight; automatic retry forbidden',
                )
                result['status'] = 'UNKNOWN_OUTCOME'
                result['jobId'] = job_id
                result['sourceMessageId'] = job.get('source_message_id')
                self.queue_result(job_id, result)
            self._set_job_state(job_id, 'UNKNOWN_OUTCOME')
            if job.get('source_message_id'):
                self.store.set_message_state(job['source_message_id'], 'PROCESSED')


def install_write_bridge() -> None:
    """Patch only the host's bridge class; all existing host/mailbox logic stays intact."""
    import sync_bridge.host as host
    host.SafeBIMBridge = WriteSafeBIMBridge
