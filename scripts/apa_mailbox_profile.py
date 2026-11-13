"""Bind the existing mailbox to an isolated, independently reopened PLN."""

import os
from pathlib import Path

from apa_release import MANIFEST, read_json, read_release, sha256, verify_member


SCHEMA = "APA_AC29_PACKAGE_READ_ONLY_PROFILE_V1"
KEYS = {"schema", "state", "receiptSha256", "releaseManifestSha256", "port"}
LEGACY_ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
LEGACY_HISTORY = LEGACY_ROOT / "apa-job-bridge-state"
APX = Path(r"C:\Program Files\Graphisoft\Archicad 29\Add-Ons\Tapir\TapirAddOn_AC29_Win.apx")


def mailbox_mutex():
    old = LEGACY_HISTORY / ".single-instance.lock"
    if old.is_file():
        return old.open("r+b")
    if LEGACY_ROOT.exists():
        raise ValueError("В установленной APA отсутствует общий файл блокировки приёмника")
    path = Path(os.environ["LOCALAPPDATA"]) / "APA" / "mailbox-owner.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a+b")


def saved_copy(state):
    from archicad_scene_run import digest

    state = Path(state).resolve(strict=True)
    manifest = read_json(state / "manifest.json")
    saved = read_json(state / "saved.json")
    reopened = read_json(state / "reopened.json")
    working = Path(manifest["scratch"]).resolve(strict=True)
    donor = Path(manifest["source"]).resolve(strict=True)
    guids = reopened["reopenedGuids"]
    if (manifest.get("schema") != "APA_AC29_NATIVE_GROUP_BATCH_V1"
            or reopened.get("status") != "LIVE_NATIVE_GROUP_BATCH_SAVED_REOPENED_PASS"
            or reopened.get("reopenVerified") is not True or reopened.get("sourceUnchanged") is not True
            or reopened.get("verificationNativeWrites") != 0
            or not isinstance(guids, list) or not guids or len(set(guids)) != len(guids)
            or len(guids) != saved["finalGuidCount"]
            or digest(guids) != reopened["reopenedGuidSetSHA256"]
            or reopened["reopenedGuidSetSHA256"] != saved["finalGuidSetSHA256"]
            or reopened["reopenedBrepSHA256"] != saved["finalBrepSHA256"]
            or working == donor or working.samefile(donor)
            or sha256(working) != saved["savedSHA256"] or reopened["savedSHA256"] != saved["savedSHA256"]
            or sha256(donor) != manifest["sourceSHA256"] or saved["sourceSHA256"] != manifest["sourceSHA256"]):
        raise ValueError("Для профиля нужна изолированная PLN с совпавшими GUID, BREP и квитанцией повторного открытия")
    return working, donor, saved, len(guids)


def make_profile(root, state, port):
    state = Path(state).resolve(strict=True)
    saved_copy(state)
    if type(port) is not int or not 19723 <= port <= 19743:
        raise ValueError("Укажите порт JSON API экземпляра Archicad 29")
    read_release(root)
    return {"schema": SCHEMA, "state": str(state), "port": port,
            "receiptSha256": sha256(state / "reopened.json"),
            "releaseManifestSha256": sha256(root / MANIFEST)}


class PackageProfile:
    def __init__(self, root, path):
        self.root = root.resolve()
        path = Path(path).resolve(strict=True)
        config = read_json(path)
        if (set(config) != KEYS or config["schema"] != SCHEMA
                or type(config["port"]) is not int or not 19723 <= config["port"] <= 19743
                or config["releaseManifestSha256"] != sha256(self.root / MANIFEST)):
            raise ValueError("Профиль приёмника относится к другой сборке APA")
        self.config = config
        self.release = read_release(self.root)
        self.state = Path(config["state"]).resolve(strict=True)
        if config["receiptSha256"] != sha256(self.state / "reopened.json"):
            raise ValueError("Квитанция повторного открытия изменилась")
        self.working, self.donor, self.saved, self.guid_count = saved_copy(self.state)
        self.port = config["port"]
        self.history = (path.parent / "apa-package-jobs").resolve()
        if self.history.is_relative_to(LEGACY_ROOT.resolve()) or self.history.is_relative_to(self.state):
            raise ValueError("Папка заданий должна быть вне установленной APA и каталога исходной квитанции")
        receipt = verify_member(self.root, self.release, "native/binary-receipt.json")
        self.native = read_json(receipt)["binary"]
        self.check_package()

    def check_package(self):
        if sha256(self.root / MANIFEST) != self.config["releaseManifestSha256"]:
            raise ValueError("Манифест комплекта изменился после привязки профиля")
        for relative in self.release["files"]:
            if relative.startswith(("scripts/", "schemas/", "archicad-addon/")) or relative in ("apa.py", "apa_release.py"):
                verify_member(self.root, self.release, relative)
        self.check_model_files()

    def check_model_files(self):
        if (sha256(self.working) != self.saved["savedSHA256"] or sha256(self.donor) != self.saved["sourceSHA256"]
                or sha256(APX) != self.native["apxSHA256"]):
            raise ValueError("PLN, защищённый исходник или установленный APX отличаются от профиля приёмника")

    def check_native(self, api):
        from archicad_scene_run import guarded_project_for_read

        guarded_project_for_read(api)
        current = api("GetAPARuntimeInfoV1", {})
        if any(current.get(key) != self.native[key] for key in ("sourceRevision", "buildIdentity")):
            raise ValueError("Загруженный APX отличается от сборки профиля")

    mutex = staticmethod(mailbox_mutex)
