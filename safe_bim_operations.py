"""Registered deterministic operations; conservative, receipt-based reconciliation.

No geometry search can prove ownership or non-application after a lost response.
Only a durable no-dispatch checkpoint permits NOT_APPLIED. APPLIED requires a
previously verified receipt bound to the exact persisted prepared contract AND
fresh full read-back of those same GUIDs. Unreceipted writes need human review.
"""
from contextlib import contextmanager
import inspect
import json
import hashlib
from typing import Any
from safe_bim_layer import SafeBIMLayer, SafeBIMError, TapirClient
from safe_bim_verification import response_items, guid_key

OPERATIONS = frozenset({'create_wall_loop', 'create_basic_slab', 'create_plinth_segment',
                        'insert_window', 'insert_door'})
METADATA = frozenset({'verticalContext', 'expectedZFingerprint'})


def normalized_params(operation, params):
    if operation not in OPERATIONS or not isinstance(params, dict):
        raise SafeBIMError('registered operation and params object required')
    clean = {k: v for k, v in params.items() if k not in METADATA}
    try:
        binding = inspect.signature(getattr(SafeBIMLayer, operation)).bind(None, **clean)
        binding.apply_defaults()
        values = dict(binding.arguments)
        values.pop('self')
        json.dumps(values, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise SafeBIMError(f'invalid operation params: {exc}') from exc
    return values


class SafeBIMOperations:
    def __init__(self, client: TapirClient):
        self.client = client
        self.layer = SafeBIMLayer(client)

    def current_project(self) -> str:
        path = response_items(self.client.call('GetProjectInfo', {})).get('projectPath')
        if not isinstance(path, str) or not path.strip():
            raise SafeBIMError('GetProjectInfo returned no projectPath')
        return path

    def prepare(self, operation, params):
        clean = normalized_params(operation, params)
        return self.layer.prepare(operation, {**clean, **{k: params[k] for k in METADATA if k in params}})

    @contextmanager
    def execution_context(self, prepared, before_write, receipt):
        with self.layer.execution_context(prepared, before_write, receipt):
            yield

    def execute(self, operation: str, params: dict[str, Any]):
        clean = normalized_params(operation, params)
        if getattr(self.layer._execution, 'value', None) is None:
            prepared = self.prepare(operation, params)
            with self.execution_context(prepared, lambda *_: None, lambda *_: None):
                return getattr(self.layer, operation)(**clean)
        return getattr(self.layer, operation)(**clean)

    def reconcile(self, operation, params, previous=None):
        ambiguous = {'classification': 'AMBIGUOUS', 'status': 'UNKNOWN_OUTCOME',
                     'readbackVerified': False, 'retryAllowed': False}
        try:
            clean = normalized_params(operation, params)
            if not isinstance(previous, dict):
                return dict(ambiguous, reason='no durable attempt evidence')
            checkpoint = previous.get('checkpoint')
            if not isinstance(checkpoint, dict) or checkpoint.get('version') != 1:
                return dict(ambiguous, reason='legacy/missing checkpoint; human reconciliation required')
            payload = checkpoint.get('payload', {})
            if payload.get('operation') != operation or normalized_params(operation, payload.get('params')) != clean:
                return dict(ambiguous, reason='checkpoint operation/params mismatch')
            if (any(checkpoint.get(k) != previous.get(k) for k in ('job_id', 'position', 'attempt'))
                    or payload.get('projectPath') != previous.get('projectPath')
                    or not checkpoint.get('attemptId')):
                return dict(ambiguous, reason='checkpoint scope mismatch')
            if checkpoint.get('dispatchStarted') is False:
                return {'classification': 'NOT_APPLIED', 'absenceProven': True,
                        'proof': 'durable checkpoint: dispatch never admitted', 'retryAllowed': True}
            prepared = payload.get('prepared')
            receipt = previous.get('result')
            if not isinstance(prepared, dict) or not isinstance(receipt, dict):
                return dict(ambiguous, reason='missing prepared contract/verified receipt')
            identity = {'job_id': previous.get('job_id'), 'position': previous.get('position'),
                        'attempt': previous.get('attempt'), 'attempt_id': checkpoint.get('attemptId'),
                        'projectPath': payload.get('projectPath')}
            if (any(v is None for v in identity.values()) or prepared.get('executionIdentity') != identity
                    or receipt.get('executionIdentity') != identity):
                return dict(ambiguous, reason='receipt is not bound to this job/step/attempt/project')
            hashed = {k: v for k, v in prepared.items() if k != 'contractHash'}
            digest = hashlib.sha256(json.dumps(hashed, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
            if (prepared.get('operation') != operation or prepared.get('params') != clean
                    or prepared.get('contractHash') != digest or receipt.get('contractHash') != digest
                    or receipt.get('operation') != operation or receipt.get('readbackVerified') is not True):
                return dict(ambiguous, reason='unverified receipt or fingerprint mismatch')
            guids = receipt.get('guids')
            if not isinstance(guids, list) or not guids or any(not isinstance(g, str) or not g for g in guids):
                return dict(ambiguous, reason='missing receipt identities')
            old = {guid_key(g) for g in prepared['preexistingGuids']}
            if any(guid_key(g) in old for g in guids):
                return dict(ambiguous, reason='foreign/pre-existing identity')
            details = self.layer.verify_saved(prepared, guids)
            return dict(receipt, status='PASS', classification='APPLIED', readback=details,
                        readbackVerified=True, retryAllowed=False)
        except Exception as exc:
            return dict(ambiguous, reason=f'reconciliation unavailable: {type(exc).__name__}: {exc}')
