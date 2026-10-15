"""128 pointer and result-binding tests; offline local handlers, never native commands."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from archicad_dynamic_commands import DynamicCommands


def escape(segment):
    return segment.replace("~", "~0").replace("/", "~1")


def fixture(case, key):
    names = {"Emit", "Accept"}
    output = {"type": "object", "properties": {"data": {
        "type": "object", "properties": {key: {
            "type": "array", "items": {"type": "integer"}}}, "required": [key]
    }}, "required": ["data"]}
    contracts = {
        "Emit": {"name": "Emit", "version": "1", "category": "OfflineFixture",
                 "parameters": {"type": "object", "additionalProperties": False},
                 "returns": output},
        "Accept": {"name": "Accept", "version": "1", "category": "OfflineFixture",
                   "parameters": {"type": "object", "properties": {
                       "value": {"type": "integer"}}, "required": ["value"],
                       "additionalProperties": False},
                   "returns": {"type": "object", "properties": {
                       "received": {"type": "integer"}}, "required": ["received"]}}
    }
    router = DynamicCommands({"common_schemas": {}, "commands": {}})
    router.add_local_provider("Fixture", contracts, {
        "Emit": lambda: {"data": {key: [case]}},
        "Accept": lambda value: {"received": value}
    }, "isolated-fixture-only", {"Emit": [], "Accept": []})
    for name in sorted(names):
        router.review_policy("AddOn.Fixture." + name, "READ_ONLY", "READ_ONLY",
                             {"source": "test-owned local fixture", "sha256": "a" * 64})
    return router


def plan(pointer):
    return {"operations": [
        {"id": "emitter", "command": "AddOn.Fixture.Emit", "params": {}},
        {"id": "consumer", "command": "AddOn.Fixture.Accept",
         "params": {"value": {"$result": {"step": "emitter", "pointer": pointer}}}}
    ]}


@pytest.mark.parametrize("case", range(64))
def test_escaped_nested_result_binding_executes_local_pipeline(case):
    keys = ["a/b", "~", "a~b/c", "0", "~0", "/~", "a~1b", "a b"]
    key = keys[case % len(keys)] + str(case)
    router = fixture(case, key)
    p = plan("/data/" + escape(key) + "/0")
    compiled = router.prepare_workflow(p)
    assert compiled["executionPermission"] is False
    assert compiled["executionOrder"] == ["emitter", "consumer"]
    out = router.run_workflow(None, compiled)
    assert out["status"] == "WORKFLOW_CALLABLE_VERIFIED"
    assert out["results"]["consumer"]["received"] == case
    assert all(event["nativeWrites"] == 0 for event in router.local_events)


@pytest.mark.parametrize("case", range(64))
def test_invalid_result_pointer_fails_before_transport(case):
    # These tokens are invalid RFC 6901 encodings or non-canonical array indices.
    # Keys deliberately exist to distinguish validation from accidental KeyError.
    key = "unsafe~2" if case % 8 == 0 else (
        "end~" if case % 8 == 1 else "valid")
    router = fixture(case, key)
    valid = "/data/" + escape(key) + "/0"
    variant = case % 8
    if variant == 0: pointer = "/data/unsafe~2/0"
    elif variant == 1: pointer = "/data/end~/0"
    elif variant == 2: pointer = "data/valid/0"
    elif variant == 3: pointer = "/data/valid/00"
    elif variant == 4: pointer = "/data/valid/-1"
    elif variant == 5: pointer = "/data/valid/+0"
    elif variant == 6: pointer = "/data/valid/-"
    else: pointer = valid + "/out-of-range"
    with pytest.raises((ValueError, KeyError, IndexError, TypeError)):
        router.prepare_workflow(plan(pointer))
