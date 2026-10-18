"""V2 side-by-side installer and composed-APA-factory contract tests.

All tests use temporary fake Windows-style sidecar files and stdlib mocks.
No vendor packages, network, Archicad, PLN/APX or production paths touched.
"""
from __future__ import annotations

from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_high_density_readonly_v2 as PROVIDER
import apa_high_density_session_factory_v2 as FACTORY
import install_apa_high_density_readonly_v2 as INSTALL


class Router:
    def __init__(self, count=6):
        self.catalog = {"commands": {
            "AddOn.APAExternalReadOnly.Original" + str(i):
                {"api": "local-python"} for i in range(count)}}
        self.policy = {k: "READ_ONLY" for k in self.catalog["commands"]}

    def operation_kind(self, name):
        return self.policy.get(name, "UNKNOWN")

    def add_local_provider(self, namespace, contracts, handlers, source, deps):
        if set(contracts) != set(handlers) or set(contracts) != set(deps):
            raise ValueError("PROVIDER_CONTRACT_MISMATCH")
        for name in contracts:
            key = "AddOn." + namespace + "." + name
            if key in self.catalog["commands"]:
                raise ValueError("PROVIDER_DUPLICATE")
            self.catalog["commands"][key] = {"api": "local-python"}

    def contract_hash(self, name):
        return "fixture-source-hash"

    def review_policy(self, name, kind, impact, evidence):
        self.policy[name] = kind


class InstallFactoryTests(unittest.TestCase):
    def make_fake_v1(self, external):
        v1 = external / "apa-readonly-v1"
        session = v1 / "session-factory-v1"
        session.mkdir(parents=True)
        vendor_python = v1 / "venv" / "Scripts"
        vendor_python.mkdir(parents=True)
        (vendor_python / "python.exe").write_text("placeholder")
        manifest = {"schema": "APA_EXTERNAL_READONLY_INSTALL_V1"}
        for key, name in (
            ("adapterSHA256", "apa_external_readonly.py"),
            ("catalogSHA256", "apa_external_catalog.py"),
            ("requirementsSHA256", "requirements-external-readonly.txt"),
        ):
            file = v1 / name
            file.write_text(key)
            manifest[key] = INSTALL.sha256(file)
        (v1 / "installation.json").write_text(json.dumps(manifest))
        factory_path = session / "apa_external_session_factory.py"
        factory_path.write_text(
            "def native_command_router(schema_path, official_commands=None, "
            "include_functional_modules=True):\n"
            "    return None\n")
        receipt = session / "session-factory-install.json"
        receipt.write_text(json.dumps({
            "schema": "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1",
            "factorySHA256": INSTALL.sha256(factory_path)}))
        return v1, factory_path, receipt

    def patched_install(self, external, v1, v1_factory, receipt):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(INSTALL, "EXTERNAL", external))
        stack.enter_context(mock.patch.object(INSTALL, "V1", v1))
        stack.enter_context(mock.patch.object(INSTALL, "V1_FACTORY", v1_factory))
        stack.enter_context(mock.patch.object(INSTALL, "V1_FACTORY_RECEIPT", receipt))
        stack.enter_context(mock.patch.object(INSTALL, "V2",
                                             external / "apa-readonly-v2"))
        stack.enter_context(mock.patch.object(INSTALL.platform, "system",
                                             return_value="Windows"))
        stack.enter_context(mock.patch.object(INSTALL.platform, "machine",
                                             return_value="AMD64"))
        return stack

    def test_preflight_does_not_write_installer_target(self):
        with tempfile.TemporaryDirectory() as td:
            external = Path(td) / "external-tools"
            v1, factory, receipt = self.make_fake_v1(external)
            self.patched_install(external, v1, factory, receipt)
            info = INSTALL.preflight()
            self.assertEqual(info["status"], "V2_SOURCE_READY_NOT_INSTALLED")
            self.assertTrue(info["targetAvailable"])
            self.assertFalse(INSTALL.V2.exists())

    def test_install_adds_only_new_v2_and_preserves_v1(self):
        with tempfile.TemporaryDirectory() as td:
            ext = Path(td) / "external-tools"
            v1, factory, receipt = self.make_fake_v1(ext)
            self.patched_install(ext, v1, factory, receipt)
            old_receipt_sha = INSTALL.sha256(receipt)
            old_factory_sha = INSTALL.sha256(factory)
            result = INSTALL.install()
            self.assertEqual(result["status"], "V2_FILES_INSTALLED_OPT_IN_NOT_ACTIVE")
            self.assertEqual(result["registeredCommands"], 0)
            self.assertEqual(INSTALL.sha256(receipt), old_receipt_sha)
            self.assertEqual(INSTALL.sha256(factory), old_factory_sha)
            self.assertEqual(result["nativeCalls"], 0)
            self.assertEqual(result["plnWrites"], 0)
            self.assertTrue((INSTALL.V2 / "apa_high_density_readonly_v2.py").is_file())
            self.assertTrue((INSTALL.V2 / "apa_high_density_session_factory_v2.py").is_file())
            self.assertFalse((v1 / "apa_high_density_readonly_v2.py").exists())

    def test_second_install_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            ext = Path(td) / "external-tools"
            v1, factory, receipt = self.make_fake_v1(ext)
            self.patched_install(ext, v1, factory, receipt)
            INSTALL.install()
            receipt_sha = INSTALL.sha256(INSTALL.V2 / "installation-v2.json")
            with self.assertRaisesRegex(ValueError, "V2_ALREADY_EXISTS"):
                INSTALL.install()
            self.assertEqual(receipt_sha,
                             INSTALL.sha256(INSTALL.V2 / "installation-v2.json"))

    def test_v2_source_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ext = Path(td) / "external-tools"
            v1, factory, receipt = self.make_fake_v1(ext)
            self.patched_install(ext, v1, factory, receipt)
            INSTALL.install()
            with (INSTALL.V2 / "apa_high_density_readonly_v2.py").open("a") as out:
                out.write("\n# unapproved drift\n")
            with self.assertRaisesRegex(ValueError, "V2_INSTALLED_FILE_HASH_DRIFT"):
                INSTALL.check()

    def test_v1_vendor_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ext = Path(td) / "external-tools"
            v1, factory, receipt = self.make_fake_v1(ext)
            self.patched_install(ext, v1, factory, receipt)
            INSTALL.install()
            (v1 / "apa_external_catalog.py").write_text("drift")
            with self.assertRaisesRegex(ValueError, "V1_INSTALL_FILE_HASH_DRIFT"):
                INSTALL.check()

    def test_v2_session_factory_rejects_tampered_factory(self):
        with tempfile.TemporaryDirectory() as td:
            ext = Path(td) / "external-tools"
            v1, original, receipt = self.make_fake_v1(ext)
            self.patched_install(ext, v1, original, receipt)
            INSTALL.install()
            v2 = INSTALL.V2
            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(FACTORY, "V1_FACTORY", original))
                stack.enter_context(mock.patch.object(FACTORY, "V1_RECEIPT", receipt))
                stack.enter_context(mock.patch.object(FACTORY, "V2_SOURCE",
                                                     v2 / "apa_high_density_readonly_v2.py"))
                stack.enter_context(mock.patch.object(FACTORY, "V2_FACTORY",
                                                     v2 / "apa_high_density_session_factory_v2.py"))
                stack.enter_context(mock.patch.object(FACTORY, "V2_RECEIPT",
                                                     v2 / "installation-v2.json"))
                old, new = FACTORY.verified_modules()
                self.assertTrue(callable(old.native_command_router))
                self.assertEqual(len(new.COMMANDS), 12)
                with (v2 / "apa_high_density_session_factory_v2.py").open("a") as file:
                    file.write("# changed\n")
                with self.assertRaisesRegex(ValueError, "V2_INSTALL_MANIFEST_OR_HASH_DRIFT"):
                    FACTORY.verified_modules()

    def test_composed_factory_keeps_six_adds_twelve_readonly(self):
        router = Router()
        old_keys = set(router.catalog["commands"])
        originals = NS(native_command_router=lambda *a, **kw: router)
        extension = NS(register=PROVIDER.register)
        with mock.patch.object(FACTORY, "verified_modules",
                               return_value=(originals, extension)):
            with mock.patch.object(PROVIDER, "verified_python",
                                   return_value=Path("C:/vendor/python.exe")):
                result = FACTORY.native_command_router("mock-schema")
        self.assertIs(result, router)
        self.assertEqual(len(router.catalog["commands"]), 18)
        self.assertEqual(old_keys & set(router.catalog["commands"]), old_keys)
        self.assertEqual(sum(x.startswith(FACTORY.V2_PREFIX)
                             for x in router.catalog["commands"]), 12)
        self.assertTrue(all(policy == "READ_ONLY"
                            for policy in router.policy.values()))

    def test_incomplete_old_six_aborts_before_v2(self):
        router = Router(count=5)
        originals = NS(native_command_router=lambda *a, **kw: router)
        v2 = NS(register=mock.Mock())
        with mock.patch.object(FACTORY, "verified_modules",
                               return_value=(originals, v2)):
            with self.assertRaisesRegex(ValueError, "V1_SIX_BASELINE_NOT_VERIFIED"):
                FACTORY.native_command_router("mock-schema")
        v2.register.assert_not_called()

    def test_incomplete_twelve_aborts(self):
        router = Router()
        originals = NS(native_command_router=lambda *a, **kw: router)
        extension = NS(register=lambda r: {"addedCommands": 11})
        with mock.patch.object(FACTORY, "verified_modules",
                               return_value=(originals, extension)):
            with self.assertRaisesRegex(ValueError,
                                        "V2_TWELVE_COMMAND_REGISTRATION_NOT_VERIFIED"):
                FACTORY.native_command_router("mock-schema")


if __name__ == "__main__":
    unittest.main()
