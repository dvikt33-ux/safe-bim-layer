"""Operator-owned runtime binding used by both generic and typed Tapir reads."""
from __future__ import annotations

import json
from pathlib import Path
import re

from apa_release import sha256 as hash_file


BRIDGE_SCHEMA = "APA_TAPIR_READ_PROFILE_V1"
LEGACY_AC30_SCHEMA = "APA_AC30_TAPIR20_READ_ONLY_V1"
CONFIG_KEYS = frozenset({"schema", "project", "projectSha256", "backup", "backupSha256",
                         "addon", "addonSha256", "port", "archicadVersion", "tapirVersion"})
CATALOG_KEYS = frozenset({"catalog", "catalogSha256"})
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?")
SHA256 = re.compile(r"[a-f0-9]{64}")


class TapirProfileError(ValueError):
    pass


def fail(reason):
    raise TapirProfileError("APA_TAPIR_" + reason)


def exact_file(raw):
    if not isinstance(raw, str) or not raw:
        fail("PATH_REQUIRED")
    path = Path(raw)
    if not path.is_absolute() or not path.is_file() or path.resolve(strict=True) != path:
        fail("UNTRUSTED_PATH")
    return path


def validate_profile_shape(config):
    if not isinstance(config, dict):
        fail("PROFILE_SCHEMA")
    keys, schema = set(config), config.get("schema")
    if schema == LEGACY_AC30_SCHEMA and keys == CONFIG_KEYS:
        if config["archicadVersion"] != 30 or config["tapirVersion"] != "2.0.0":
            fail("VERSION_PROFILE")
    elif schema == BRIDGE_SCHEMA and keys in (CONFIG_KEYS, CONFIG_KEYS | CATALOG_KEYS):
        if (type(config["archicadVersion"]) is not int or config["archicadVersion"] < 25
                or not isinstance(config["tapirVersion"], str) or not VERSION.fullmatch(config["tapirVersion"])):
            fail("VERSION_PROFILE")
        if "catalog" in config:
            if not isinstance(config["catalogSha256"], str) or not SHA256.fullmatch(config["catalogSha256"]):
                fail("INVALID_CATALOG_SHA256")
            exact_file(config["catalog"])
    else:
        fail("PROFILE_SCHEMA")
    if type(config["port"]) is not int or not 1024 <= config["port"] <= 65535:
        fail("INVALID_PORT")


def profile_from_path(path):
    path = exact_file(str(path))
    if path.stat().st_size > 16_384:
        fail("PROFILE_TOO_LARGE")
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    validate_profile_shape(config)
    paths = {key: exact_file(config[key]) for key in ("project", "backup", "addon")}
    if len(set(paths.values())) != 3 or any(paths[key].suffix.casefold() != suffix for key, suffix in
                                           (("project", ".pln"), ("backup", ".pln"), ("addon", ".apx"))):
        fail("INVALID_SOURCE_KINDS")
    for key in paths:
        digest = config[key + "Sha256"]
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            fail("INVALID_SHA256")
    if config["projectSha256"] != config["backupSha256"]:
        fail("BASELINE_BACKUP_NOT_IDENTICAL")
    check_files(config, "FILE_HASH_DRIFT_")
    return config


def check_files(config, reason_prefix):
    for key in ("project", "backup", "addon"):
        if hash_file(exact_file(config[key])) != config[key + "Sha256"]:
            fail(reason_prefix + key.upper())


def guard(config, call):
    check_files(config, "FILE_DRIFT_")
    project = call("GetProjectInfo", {})
    path = project.get("projectPath")
    if (not isinstance(path, str) or path.casefold() != config["project"].casefold()
            or project.get("isUntitled") is not False or project.get("isTeamwork") is not False):
        fail("WRONG_OPEN_PROJECT")
    product = call("API.GetProductInfo", {})
    if product.get("version") != config["archicadVersion"]:
        fail("ARCHICAD_VERSION_DRIFT")
    addon = call("GetAddOnVersion", {})
    if addon.get("version") != config["tapirVersion"]:
        fail("TAPIR_VERSION_DRIFT")
    return dict(project=path, archicadVersion=product["version"], archicadBuild=product.get("buildNumber"),
                tapirVersion=addon["version"], addonSha256=config["addonSha256"])
