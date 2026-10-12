#!/usr/bin/env python3
"""State-aware compiled-block resolver.

Primary runtime path:
exact object route -> requested module/depth -> dependency closure -> reuse completed
blocks from project_state -> evaluate machine guards -> edge-scoped FAST PACK only
when a real unresolved normative edge is touched.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


class ResolutionError(RuntimeError):
    """Repository/runtime configuration error: fail hard, do not hide behind fallback."""


class RequestResolutionError(ResolutionError):
    """User-request gap that may legitimately enter the minimal reserve path."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover
        raise ResolutionError(f"{path}: YAML read/parse error: {exc}") from exc


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _ordered_unique(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


class CompiledBlockResolver:
    def __init__(self, repo_root: Path | str, object_type: str):
        self.root = Path(repo_root).resolve()
        self.object_type = object_type
        self.route_path = self.root / "01_Normative_Base/_Machine/routes/objects" / f"{object_type}.yaml"
        if not self.route_path.exists():
            raise ResolutionError(f"exact object route is missing: {self.route_path}")
        self.route = _load_yaml(self.route_path)
        if self.route.get("object_type") != object_type:
            raise ResolutionError(
                f"route object_type mismatch: expected {object_type}, got {self.route.get('object_type')}"
            )
        scope = self.route.get("scope", {})
        if scope.get("cross_class_fallback") != "forbidden":
            raise ResolutionError("cross_class_fallback must be forbidden")
        if scope.get("parent_fallback") != "forbidden":
            raise ResolutionError("parent_fallback must be forbidden")

        catalog_ref = self.route.get("block_catalog")
        if not catalog_ref:
            raise ResolutionError("route has no block_catalog")
        self.catalog_path = self.root / str(catalog_ref)
        self.catalog = _load_yaml(self.catalog_path)
        self.policy = _load_yaml(self.root / "04_Code_Generation/block_resolution_policy.yaml")
        self.blocks: Dict[str, Dict[str, Any]] = {}
        self._load_blocks()
        self.block_prefixes = {block_id.split('.', 1)[0] for block_id in self.blocks}

    def _load_blocks(self) -> None:
        implemented = self.catalog.get("implemented_blocks", {})
        if not isinstance(implemented, dict):
            raise ResolutionError("implemented_blocks must be a mapping")
        for block_id, entry in implemented.items():
            path = self.root / str((entry or {}).get("file", ""))
            if not path.exists():
                raise ResolutionError(f"catalog block file missing for {block_id}: {path}")
            data = _load_yaml(path)
            if data.get("block_id") != block_id:
                raise ResolutionError(f"catalog/file block_id mismatch for {block_id}")
            object_classes = _as_list(data.get("object_scope", {}).get("object_classes"))
            if self.object_type not in object_classes:
                raise ResolutionError(
                    f"block {block_id} does not explicitly include exact object type {self.object_type}"
                )
            self.blocks[block_id] = {
                "entry": entry or {},
                "data": data,
                "path": path,
                "requires": _as_list(data.get("normative_closure", {}).get("dependency_blocks")),
                "release_status": data.get("release_status"),
                "guard_rules": _as_list(data.get("runtime_interface", {}).get("guard_rules")),
                "unresolved_dependencies": _as_list(
                    data.get("normative_closure", {}).get("unresolved_dependencies")
                ),
            }

    def _block_id_from_route_path(self, path_text: str) -> str:
        path = self.root / str(path_text)
        if not path.exists():
            raise ResolutionError(f"route points to missing compiled block: {path_text}")
        block_id = _load_yaml(path).get("block_id")
        if not block_id or block_id not in self.blocks:
            raise ResolutionError(f"route path is not a registered block: {path_text}")
        return block_id

    def target_blocks(
        self,
        module: Optional[str] = None,
        depth: Optional[str] = None,
        special: Optional[str] = None,
        explicit_blocks: Optional[Iterable[str]] = None,
    ) -> List[str]:
        if explicit_blocks:
            targets = list(explicit_blocks)
            for block_id in targets:
                if block_id not in self.blocks:
                    prefix = str(block_id).split('.', 1)[0]
                    code = 'BLOCK_SCOPE_MISMATCH' if prefix not in self.block_prefixes else 'IMPLEMENTED_BLOCK_MISSING'
                    raise RequestResolutionError(
                        f"explicit block is not implemented in exact {self.object_type} route: {block_id}",
                        code,
                    )
            return targets

        if special == "elements":
            candidates = [
                block_id
                for block_id, meta in self.blocks.items()
                if meta["entry"].get("module") == "architecture" and block_id.endswith(".ELEMENTS.CORE")
            ]
            if len(candidates) != 1:
                raise ResolutionError(f"elements special resolver expected exactly one block, got {candidates}")
            return candidates

        if not module or not depth:
            raise RequestResolutionError(
                "module and depth are required unless special/explicit resolver is used",
                "REQUESTED_DEPTH_NOT_IMPLEMENTED_AND_LOWER_DEPTH_INSUFFICIENT",
            )
        try:
            refs = self.route["compiled_blocks"][module][depth]
        except KeyError as exc:
            raise RequestResolutionError(
                f"route has no implemented depth {module}.{depth}",
                "REQUESTED_DEPTH_NOT_IMPLEMENTED_AND_LOWER_DEPTH_INSUFFICIENT",
            ) from exc
        return [self._block_id_from_route_path(ref) for ref in refs]

    def dependency_closure(self, targets: Iterable[str]) -> List[str]:
        ordered: List[str] = []
        state: Dict[str, int] = {}
        stack: List[str] = []

        def visit(block_id: str) -> None:
            if block_id not in self.blocks:
                raise ResolutionError(f"dependency block missing: {block_id}")
            mark = state.get(block_id, 0)
            if mark == 2:
                return
            if mark == 1:
                raise ResolutionError("dependency cycle: " + " -> ".join(stack + [block_id]))
            state[block_id] = 1
            stack.append(block_id)
            for dep in self.blocks[block_id]["requires"]:
                visit(dep)
            stack.pop()
            state[block_id] = 2
            ordered.append(block_id)

        for target in targets:
            visit(target)
        return ordered

    @staticmethod
    def _guard_matches(rule: Dict[str, Any], runtime_inputs: Dict[str, Any]) -> bool:
        key = rule.get("input")
        op = rule.get("operator")
        present = key in runtime_inputs
        value = runtime_inputs.get(key)
        if op == "missing":
            return not present or value is None
        if op == "present":
            return present and value is not None
        if op == "equals":
            return value == rule.get("value")
        if op == "not_equals":
            return value != rule.get("value")
        if op == "in":
            return value in _as_list(rule.get("values"))
        if op == "not_in":
            return value not in _as_list(rule.get("values"))
        raise ResolutionError(f"unknown guard operator {op!r} in rule {rule.get('id')}")

    def _evaluate_guards(self, closure: Iterable[str], runtime_inputs: Dict[str, Any]) -> Dict[str, List[str]]:
        missing_inputs: List[str] = []
        blocked_outputs: List[str] = []
        required_edges: List[str] = []
        add_dependencies: List[str] = []
        warnings: List[str] = []

        for block_id in closure:
            for rule in self.blocks[block_id]["guard_rules"]:
                if not self._guard_matches(rule, runtime_inputs):
                    continue
                effect = rule.get("effect")
                if effect == "missing_input":
                    key = rule.get("output_key") or rule.get("input")
                    if key and key not in missing_inputs:
                        missing_inputs.append(str(key))
                elif effect == "block_output":
                    key = rule.get("output_key") or rule.get("id")
                    if key and key not in blocked_outputs:
                        blocked_outputs.append(str(key))
                elif effect == "require_edge":
                    edge_id = rule.get("edge_id")
                    if edge_id and edge_id not in required_edges:
                        required_edges.append(str(edge_id))
                elif effect == "add_dependency":
                    dep = rule.get("dependency_block")
                    if dep:
                        if dep not in self.blocks:
                            raise ResolutionError(f"guard requests unknown dependency block {dep}")
                        if dep not in add_dependencies:
                            add_dependencies.append(str(dep))
                elif effect == "warning":
                    pass
                else:
                    raise ResolutionError(f"unknown guard effect {effect!r} in rule {rule.get('id')}")
                message = rule.get("message")
                if message and message not in warnings:
                    warnings.append(str(message))

        return {
            "missing_inputs": missing_inputs,
            "blocked_outputs": blocked_outputs,
            "required_edges": required_edges,
            "add_dependencies": add_dependencies,
            "warnings": warnings,
        }

    def resolve(self, request: Dict[str, Any], project_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        state = deepcopy(project_state or {})
        completed = set(_as_list(state.get("completed_block_ids")))
        runtime_inputs = dict(request.get("runtime_inputs") or {})

        try:
            targets = self.target_blocks(
                module=request.get("module"),
                depth=request.get("depth"),
                special=request.get("special"),
                explicit_blocks=request.get("explicit_blocks"),
            )
        except RequestResolutionError as exc:
            return {
                "targets": [],
                "selected_closure": [],
                "new_blocks": [],
                "reused_dependencies": [],
                "skipped_targets": [],
                "fast_pack": True,
                "fallback_reasons": [exc.code],
                "fallback_scope": [],
                "normative_authority": False,
                "missing_inputs": [],
                "blocked_outputs": [],
                "warnings": [str(exc)],
            }

        closure = self.dependency_closure(targets)
        guard_result = self._evaluate_guards(closure, runtime_inputs)
        if guard_result["add_dependencies"]:
            closure = self.dependency_closure(closure + guard_result["add_dependencies"])
            guard_result = self._evaluate_guards(closure, runtime_inputs)

        new_blocks = [block_id for block_id in closure if block_id not in completed]
        reused_direct: List[str] = []
        for block_id in new_blocks:
            for dep in self.blocks[block_id]["requires"]:
                if dep in completed and dep not in reused_direct:
                    reused_direct.append(dep)
        skipped_targets = [block_id for block_id in targets if block_id in completed]

        fallback_reasons: List[str] = []
        fallback_scope: List[str] = []
        if request.get("touches_unresolved_normative_edge"):
            fallback_reasons.append("REQUEST_TOUCHES_UNRESOLVED_NORMATIVE_EDGE")
            fallback_scope.extend(_as_list(request.get("normative_edge_ids")))
        if request.get("stale_revision_affects_request"):
            fallback_reasons.append("BLOCK_STALE_SOURCE_REVISION_AFFECTS_REQUEST")
        if guard_result["required_edges"]:
            fallback_reasons.append("REQUEST_TOUCHES_UNRESOLVED_NORMATIVE_EDGE")
            fallback_scope.extend(guard_result["required_edges"])

        normative_authority = bool(targets) and all(
            self.blocks[block_id]["release_status"] == "audited_ready" for block_id in targets
        )

        return {
            "targets": targets,
            "selected_closure": closure,
            "new_blocks": new_blocks,
            "reused_dependencies": reused_direct,
            "skipped_targets": skipped_targets,
            "fast_pack": bool(fallback_reasons),
            "fallback_reasons": _ordered_unique(fallback_reasons),
            "fallback_scope": _ordered_unique(fallback_scope),
            "normative_authority": normative_authority,
            "missing_inputs": guard_result["missing_inputs"],
            "blocked_outputs": guard_result["blocked_outputs"],
            "warnings": guard_result["warnings"],
        }

    def mark_completed(self, project_state: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        state = deepcopy(project_state)
        selected = _as_list(state.get("selected_block_ids"))
        completed = _as_list(state.get("completed_block_ids"))
        block_state = dict(state.get("block_state") or {})

        for block_id in result.get("selected_closure", []):
            if block_id not in selected:
                selected.append(block_id)
        for block_id in result.get("new_blocks", []):
            if block_id not in completed:
                completed.append(block_id)
            block_data = self.blocks[block_id]["data"]
            block_state[block_id] = {
                "block_version": str(block_data.get("version", "")),
                "release_status": block_data.get("release_status"),
                "runtime_status": "completed",
                "input_hash": "",
                "output_hash": "",
                "source_revision_hash": str(
                    block_data.get("normative_closure", {}).get("source_revision_hash", "")
                ),
                "normative_authority": block_data.get("release_status") == "audited_ready",
                "unresolved_normative_edges": _as_list(
                    block_data.get("normative_closure", {}).get("unresolved_dependencies")
                ),
            }

        state["selected_block_ids"] = selected
        state["completed_block_ids"] = completed
        state["block_state"] = block_state
        state["fallback_state"] = {
            "active": bool(result.get("fast_pack")),
            "engine": "FAST_PACK" if result.get("fast_pack") else "none",
            "reason_codes": _as_list(result.get("fallback_reasons")),
            "active_edge_ids": _as_list(result.get("fallback_scope")),
            "pack_version": "",
            "pack_hash": "",
        }
        return state


def create_empty_state(object_type: str, object_subclass: str = "", jurisdiction: str = "RU") -> Dict[str, Any]:
    return {
        "project_id": "runtime-regression",
        "object_profile": {
            "object_class": object_type,
            "object_subclass": object_subclass,
            "active_functions": [],
            "jurisdiction": jurisdiction,
        },
        "module_profile": {},
        "route_manifest_version": "",
        "selected_block_ids": [],
        "completed_block_ids": [],
        "block_state": {},
        "stage_status": {},
        "elements": {},
        "interfaces": {},
        "fallback_state": {
            "active": False,
            "engine": "none",
            "reason_codes": [],
            "active_edge_ids": [],
            "pack_version": "",
            "pack_hash": "",
        },
        "unresolved_conflicts": [],
    }
