"""Typed contracts and serializable Stage 2 job/evidence records."""
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import math
from typing import Any


class State(str, Enum):
    RECEIVED = 'RECEIVED'
    OBSERVING = 'OBSERVING'
    PLANNING = 'PLANNING'
    EXECUTING = 'EXECUTING'
    READING_BACK = 'READING_BACK'
    AUDITING = 'AUDITING'
    REPLANNING = 'REPLANNING'
    VERIFIED = 'VERIFIED'
    WAITING_FOR_DATA = 'WAITING_FOR_DATA'
    BLOCKED = 'BLOCKED'
    UNKNOWN_OUTCOME = 'UNKNOWN_OUTCOME'


class Verdict(str, Enum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    NOT_VERIFIED = 'NOT_VERIFIED'
    DATA_MISSING = 'DATA_MISSING'
    CONFLICT = 'CONFLICT'
    BLOCKED_BY_TRANSPORT = 'BLOCKED_BY_TRANSPORT'


def json_value(value):
    # Reject NaN/Infinity and non-JSON payloads before persisting evidence.
    json.dumps(value, allow_nan=False)


def nonempty(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string')


@dataclass(frozen=True)
class Criterion:
    id: str
    required: bool
    check: str
    expected: Any
    tolerance: float = 0.0
    correctable: bool = False

    def __post_init__(self):
        nonempty(self.id, 'criterion id')
        nonempty(self.check, 'check')
        if type(self.required) is not bool or type(self.correctable) is not bool:
            raise ValueError('required and correctable must be booleans')
        if isinstance(self.tolerance, bool) or not isinstance(self.tolerance, (int, float)) or not math.isfinite(self.tolerance) or self.tolerance < 0:
            raise ValueError('tolerance must be a finite nonnegative number')
        json_value(self.expected)


@dataclass(frozen=True)
class AcceptanceContract:
    goalId: str
    criteria: tuple[Criterion, ...]

    def __post_init__(self):
        nonempty(self.goalId, 'goalId')
        if not self.criteria or not all(isinstance(c, Criterion) for c in self.criteria):
            raise ValueError('criteria must contain typed criteria')
        if len({c.id for c in self.criteria}) != len(self.criteria):
            raise ValueError('criterion IDs must be unique')
        if not any(c.required for c in self.criteria):
            raise ValueError('at least one required criterion is necessary')

    @classmethod
    def from_dict(cls, value):
        if set(value) != {'goalId', 'criteria'} or not isinstance(value['criteria'], list):
            raise ValueError('contract requires goalId and criteria only')
        return cls(value['goalId'], tuple(Criterion(**c) for c in value['criteria']))


@dataclass(frozen=True)
class Fact:
    actual: Any = None
    status: str = 'OBSERVED'
    evidenceRefs: tuple[str, ...] = ()

    def __post_init__(self):
        if self.status not in {'OBSERVED', 'NOT_VERIFIED', 'DATA_MISSING', 'CONFLICT', 'BLOCKED_BY_TRANSPORT'}:
            raise ValueError('fact status must describe evidence, not an acceptance verdict')
        json_value(self.actual)
        if not isinstance(self.evidenceRefs, (tuple, list)) or not all(isinstance(r, str) and r for r in self.evidenceRefs):
            raise ValueError('evidenceRefs must contain reference strings')


@dataclass(frozen=True)
class Observation:
    modelIdentity: str
    modelHash: str
    facts: dict[str, Fact]
    evidence: dict[str, Any]
    provenance: str = 'FIXTURE'

    def __post_init__(self):
        nonempty(self.modelIdentity, 'modelIdentity')
        nonempty(self.modelHash, 'modelHash')
        if self.provenance != ('LIVE' if isinstance(self, LiveObservation) else 'FIXTURE'):
            raise ValueError('Stage 2 accepts fixture evidence only')
        if not isinstance(self.facts, dict) or not all(isinstance(k, str) and isinstance(v, Fact) for k, v in self.facts.items()):
            raise ValueError('facts must map check names to typed Fact records')
        if not isinstance(self.evidence, dict):
            raise ValueError('evidence must map references to retained payloads')
        json_value(self.evidence)


@dataclass(frozen=True)
class LiveObservation(Observation):
    provenance: str = 'LIVE'


@dataclass(frozen=True)
class Action:
    type: str
    parameters: dict[str, Any]

    def __post_init__(self):
        if self.type != 'create_wall':
            raise ValueError('Stage 2 mock action allowlist contains create_wall only')
        if not isinstance(self.parameters, dict):
            raise ValueError('parameters must be an object')
        json_value(self.parameters)


@dataclass(frozen=True)
class PlannerDecision:
    status: str
    action: Action | None = None
    reason: str = ''
    plannedAgainstModelIdentity: str | None = None
    plannedAgainstModelHash: str | None = None

    def __post_init__(self):
        if self.status not in {'PLANNED', 'WAITING_FOR_DATA', 'BLOCKED'}:
            raise ValueError('invalid planner status')
        if (self.status == 'PLANNED') != isinstance(self.action, Action):
            raise ValueError('only PLANNED decisions must carry a typed Action')
        for value in (self.plannedAgainstModelIdentity, self.plannedAgainstModelHash):
            if value is not None:
                nonempty(value, 'planning fingerprint')


@dataclass(frozen=True)
class ModelFingerprint:
    modelIdentity: str
    modelHash: str
    provenance: str = 'FIXTURE'

    def __post_init__(self):
        nonempty(self.modelIdentity, 'modelIdentity')
        nonempty(self.modelHash, 'modelHash')
        if self.provenance != ('LIVE' if isinstance(self, LiveModelFingerprint) else 'FIXTURE'):
            raise ValueError('Stage 2 accepts fixture fingerprints only')


@dataclass(frozen=True)
class LiveModelFingerprint(ModelFingerprint):
    provenance: str = 'LIVE'


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    mutationAttempted: bool
    readbackRequired: bool
    details: dict[str, Any] = field(default_factory=dict)
    executionMode: str = 'OFFLINE'

    def __post_init__(self):
        if self.status not in {'PASS', 'FAIL', 'BLOCKED', 'UNKNOWN_OUTCOME'}:
            raise ValueError('invalid executor status')
        if type(self.mutationAttempted) is not bool or type(self.readbackRequired) is not bool:
            raise ValueError('execution flags must be booleans')
        if self.executionMode != ('LIVE' if isinstance(self, LiveExecutionResult) else 'OFFLINE'):
            raise ValueError('live execution is unavailable in Stage 2')
        if not isinstance(self.details, dict):
            raise ValueError('details must be an object')
        json_value(self.details)


@dataclass(frozen=True)
class LiveExecutionResult(ExecutionResult):
    executionMode: str = 'LIVE'


@dataclass(frozen=True)
class AuditCriterion:
    id: str
    required: bool
    expected: Any
    actual: Any
    verdict: Verdict
    evidenceRefs: tuple[str, ...]
    correctable: bool = False


@dataclass
class Iteration:
    iteration: int
    stateBefore: State
    observation: Observation | None = None
    plannerDecision: PlannerDecision | None = None
    executorRequest: Action | None = None
    executorResult: ExecutionResult | None = None
    readback: Observation | None = None
    auditResult: list[AuditCriterion] | None = None
    observedModelHash: str | None = None
    planningModelHash: str | None = None
    preExecutionFingerprint: ModelFingerprint | None = None
    staleVerdict: str | None = None
    decisionInvalidated: bool = False
    actionFingerprint: str | None = None
    auditFingerprint: str | None = None
    progressSignature: str | None = None
    noProgressCount: int = 0


@dataclass
class Job:
    goalId: str
    specification: str
    acceptanceCriteria: tuple[Criterion, ...]
    maxIterations: int
    createdAt: str
    updatedAt: str
    state: State = State.RECEIVED
    iteration: int = 0
    observedModelIdentity: str | None = None
    observedModelHash: str | None = None
    actions: list[Action] = field(default_factory=list)
    auditHistory: list[list[AuditCriterion]] = field(default_factory=list)
    iterations: list[Iteration] = field(default_factory=list)
    evidenceTrail: list[dict[str, Any]] = field(default_factory=list)
    finalStatus: str | None = None
    terminalReason: str | None = None
    executionMode: str = 'OFFLINE'
    liveMutationAttempted: bool = False
    noProgressLimit: int = 2
    noProgressCount: int = 0

    def to_dict(self):
        return asdict(self)
