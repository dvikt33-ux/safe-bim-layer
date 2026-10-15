"""128 forged-ticket and write-scope variants; zero native calls by construction."""
import copy
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from archicad_dynamic_commands import DynamicCommands


def synthetic_router():
    row = dict(name="ModifySynthetic", version="1", category="Isolated security",
               parameters=dict(type="object", required=["value", "elementId"],
                   additionalProperties=False,
                   properties={"value": {"type": "integer"},
                               "elementId": {"type": "object",
                                             "required": ["guid"],
                                             "additionalProperties": False,
                                             "properties": {"guid": {"type": "string"}}}}),
               returns={"type": "object", "properties": {"success": {"type": "boolean"}}})
    r = DynamicCommands(dict(common_schemas={}, commands={"ModifySynthetic": row}))
    r.review_policy("ModifySynthetic", "MODIFY", "MODEL",
                    {"source": "offline synthetic contract", "sha256": "a" * 64})
    return r


def payload(case):
    return {"value": case, "elementId": {"guid": "GUID_" + str(case)}}


@pytest.mark.parametrize("case", range(64))
def test_dynamic_ticket_tamper_is_rejected_before_any_transport(case):
    r = synthetic_router()
    caller = payload(case)
    ticket = r.prepare("ModifySynthetic", caller)
    caller["value"] = -999  # ticket is an immutable deep snapshot
    assert ticket["parameters"]["value"] == case
    assert ticket["nativeWritePermission"] is False
    assert r.validate(ticket) == ticket
    tampered = copy.deepcopy(ticket)
    mode = case % 8
    if mode == 0: tampered["hash"] = "0" * 64
    elif mode == 1: tampered["parameters"]["value"] += 1
    elif mode == 2: tampered["catalogHash"] = "0" * 64
    elif mode == 3: tampered["effect"] = "READ_ONLY"
    elif mode == 4: tampered["policyHash"] = "0" * 64
    elif mode == 5: tampered["command"] = "UnknownSynthetic"
    elif mode == 6: tampered["nativeWritePermission"] = True
    else: tampered["schema"] = "FORGED"
    with pytest.raises(ValueError):
        r.validate(tampered)
    with pytest.raises(ValueError, match="SOURCE_REVIEWED_READ_ONLY_EFFECT_REQUIRED"):
        r.read(None, ticket, reviewed_read_only=True)


@pytest.mark.parametrize("case", range(64, 128))
def test_write_scope_tamper_or_unknown_target_is_rejected(case):
    r = synthetic_router()
    ticket = r.prepare("ModifySynthetic", payload(case))
    target = payload(case)["elementId"]["guid"]
    with pytest.raises(ValueError, match="DYNAMIC_ELEMENT_TARGET_OUTSIDE_AUTHORIZED_SCOPE"):
        r.scope(ticket, {"path": "isolated.pln"}, [], [], "test-only", "MODEL")
    scope = r.scope(ticket, {"path": "isolated.pln"}, [target], [], "test-only", "MODEL")
    assert scope["affectedGuids"] == [target.lower()]
    assert r.qualify_scope(scope, "ModifySynthetic", ticket["parameters"], ticket["hash"]) is None
    broken = copy.deepcopy(scope)
    command, parameters, hash_value = "ModifySynthetic", ticket["parameters"], ticket["hash"]
    mode = case % 8
    if mode == 0: broken["hash"] = "0" * 64
    elif mode == 1: broken["binding"]["path"] = "changed.pln"
    elif mode == 2: broken["affectedGuids"] = ["different"]
    elif mode == 3: broken["authorizationRef"] = ""
    elif mode == 4: broken["ticket"]["parameters"]["value"] += 1
    elif mode == 5: parameters = payload(case + 1)
    elif mode == 6: hash_value = "0" * 64
    else: r.register_availability("ModifySynthetic", False)
    with pytest.raises(ValueError):
        r.qualify_scope(broken, command, parameters, hash_value)
