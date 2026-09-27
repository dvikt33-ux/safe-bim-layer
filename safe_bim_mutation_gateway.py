"""The only admission path for a physical Tapir mutation.

Public TapirClient.call may issue an allowlisted read. Model, session, and
attribute mutations reach transport only through this gateway, and only after
one schema/runtime agreement check for the step.
"""
from __future__ import annotations

from contextlib import contextmanager
import threading

from safe_bim_command_policy import (
    ADMITTED_MODEL_COMMANDS, ADMITTED_SESSION_COMMANDS, DENIED_FROM_NORMAL_EXECUTION,
    CommandClass, PolicyError, assert_single_create_item, classify, schema_provider_version,
)
from safe_bim_layer import SafeBIMError
from safe_bim_tapir_compat import SUPPORTED_TAPIR_VERSION, assert_tapir_write_allowed

_permit = threading.local()


@contextmanager
def transport_permit():
    previous = getattr(_permit, 'allowed', False)
    _permit.allowed = True
    try:
        yield
    finally:
        _permit.allowed = previous


def require_transport_permit():
    if not getattr(_permit, 'allowed', False):
        raise SafeBIMError('Tapir transport refused without mutation admission')


class MutationGateway:
    def __init__(self, client):
        self.client = client
        self.admitted = False
        self.expected_command = None

    def begin_step(self, command: str) -> str:
        """One authoritative schema and version check for this physical step."""
        if classify(command) != CommandClass.MODEL_MUTATION or command not in ADMITTED_MODEL_COMMANDS:
            raise SafeBIMError(f'{command!r} is not an admitted model mutation')
        provider = schema_provider_version(getattr(self.client, 'schema', None))
        if provider != SUPPORTED_TAPIR_VERSION:
            raise SafeBIMError(
                f'schema provider {provider!r} is not {SUPPORTED_TAPIR_VERSION}; physical writes blocked')
        version = assert_tapir_write_allowed(self.client)
        self.admitted = True
        self.expected_command = command
        return version

    def end_step(self):
        self.admitted = False
        self.expected_command = None

    @contextmanager
    def session_if_needed(self):
        """Admit ChangeWindow when story activation is not already inside a step."""
        if self.admitted:
            yield
            return
        provider = schema_provider_version(getattr(self.client, 'schema', None))
        if provider != SUPPORTED_TAPIR_VERSION:
            raise SafeBIMError(
                f'schema provider {provider!r} is not {SUPPORTED_TAPIR_VERSION}; session mutation blocked')
        assert_tapir_write_allowed(self.client)
        self.admitted = True
        self.expected_command = None
        try:
            yield
        finally:
            self.end_step()

    def dispatch(self, command: str, params: dict):
        kind = classify(command)
        if kind == CommandClass.READ_ONLY:
            raise SafeBIMError('reads do not use the mutation gateway')
        if kind == CommandClass.UNKNOWN or not is_known_mutation(kind):
            raise SafeBIMError(f'unknown or unclassified command {command!r} is refused')
        if command in DENIED_FROM_NORMAL_EXECUTION:
            raise SafeBIMError(f'{command} is denied from normal execution')
        if not self.admitted:
            raise SafeBIMError(f'{command} refused without an admitted step')
        if kind == CommandClass.MODEL_MUTATION:
            if command != self.expected_command or command not in ADMITTED_MODEL_COMMANDS:
                raise SafeBIMError(f'{command} does not match the admitted step')
            try:
                assert_single_create_item(command, params)
            except PolicyError as exc:
                raise SafeBIMError(str(exc)) from exc
        elif kind == CommandClass.SESSION_MUTATION:
            if command not in ADMITTED_SESSION_COMMANDS:
                raise SafeBIMError(f'{command} is not an admitted session mutation')
        else:
            raise SafeBIMError(f'{command} mutation class is not admitted by this runtime')
        with transport_permit():
            return self.client.transport(command, params)


def is_known_mutation(kind: CommandClass) -> bool:
    return kind in {
        CommandClass.SESSION_MUTATION,
        CommandClass.MODEL_MUTATION,
        CommandClass.ATTRIBUTE_MUTATION,
    }
