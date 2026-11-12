"""Use the existing TDK Wall.Ensure contract through an APA read-only route."""

import importlib.util
import hashlib
import json
from pathlib import Path

from apa_release import read_release, verify_member


VENDOR = "local-components/tdk_wall_ensure.py"
READS = frozenset({"GetElementsByType", "GetAddOnVersion",
                   "GetFavoritesByType", "GetAllProperties", "GetPropertyValuesOfElements",
                   "GetDetailsOfElements"})


def vendor_module(root):
    release = read_release(root)
    if VENDOR not in release["files"]:
        raise ValueError("Для Wall.Ensure нужен локальный Windows-комплект с компонентом TDK")
    path = verify_member(root, release, VENDOR)
    spec = importlib.util.spec_from_file_location("apa_packaged_tdk_wall_ensure", path)
    vendor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vendor)
    return vendor


class ReadOnlyTransport:
    def __init__(self, router, api, product):
        self.router = router
        self.evidence_api = api
        self.product = product

    def api(self, command, parameters=None, *, mutation=False):
        if mutation:
            raise ValueError(f"Wall.Ensure запросил запись в режиме сверки: {command}")
        if command == "API.GetProductInfo":
            return self.product
        if command == "API.GetElementsByType":
            command = "GetElementsByType"
        if command not in READS or self.router.operation_kind(command) != "READ_ONLY":
            raise ValueError(f"Команда Wall.Ensure вне области чтения APA: {command}")
        ticket = self.router.prepare(command, parameters or {})
        return self.router.read(self.evidence_api, ticket, reviewed_read_only=True)

    tapir = api


def inspect_wall(root, payload_path, profile_path=None, journal_path=None, evidence_dir=None):
    vendor = vendor_module(root)
    raw = payload_path.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    desired = vendor.validate_payload(payload)
    # Reject non-finite vendor numbers before passing data to the BIM contracts.
    json.dumps(desired, allow_nan=False)
    receipt = {"status": "TDK_WALL_PAYLOAD_NORMALIZED", "operationId": payload["operationId"],
               "payloadSha256": hashlib.sha256(raw).hexdigest(), "desiredState": desired,
               "desiredStateSha256": vendor.state_hash(desired), "executionPermission": False,
               "nativeCalls": 0, "modelWrites": 0}
    if profile_path is None:
        return receipt

    from apa import load_router
    from apa_mailbox_profile import PackageProfile
    import archicad_project_accelerator as core

    profile = PackageProfile(root, profile_path)
    evidence_dir.mkdir()
    core.RUN.bind_authorized_saved_copy(profile.port, str(profile.working), profile.working.stem,
                                        profile.saved["savedSHA256"], "APA_TDK_WALL_READ_ONLY_PROFILE")
    api = core.EvidenceAPI(core.native_transport, evidence_dir, execute=False)
    profile.check_native(api)
    expected_guids = core.inventory_guids(api)
    if len(expected_guids) != profile.guid_count or core.RUN.digest(sorted(expected_guids)) != profile.saved["finalGuidSetSHA256"]:
        raise ValueError("GUID открытой PLN отличаются от подтверждённой копии")
    router = load_router()
    for command in READS:
        router.review_policy(command, "READ_ONLY", "READ_ONLY",
                             {"source": "TDK Wall.Ensure fixed read calls and pinned Tapir 1.5.10 export",
                              "sha256": router.contract_hash(command)})
    journal = vendor.Journal(journal_path or evidence_dir / "tdk-journal.jsonl")
    runtime = vendor.WallEnsureRuntime(ReadOnlyTransport(router, api, core.archicad29(api)),
                                       journal, core.RUN.EXPECTED_TAPIR, 29)
    decision = runtime.ensure(payload, commit=False)
    if api.write_attempts or core.inventory_guids(api) != expected_guids:
        raise ValueError("Состав модели изменился при сверке Wall.Ensure")
    profile.check_model_files()
    return dict(receipt, status="TDK_WALL_READBACK_PREVIEW", decision=decision,
                nativeCalls=sum(api.calls.values()))
