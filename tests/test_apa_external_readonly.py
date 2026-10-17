"""Focused safety checks for newly added APA external read-only bridge."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_external_readonly as A
import apa_external_catalog as Catalog
import apa_external_router_activation as Activation
import apa_external_session_factory as Session
import upgrade_apa_external_readonly_clash as Upgrade
import install_apa_external_session_factory as PersistentFactory


class ExternalReadonlyTests(unittest.TestCase):
    def test_source_extension_enforced_before_vendor_call(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "unexpected.txt"
            p.write_text("not an IFC")
            with self.assertRaisesRegex(ValueError, "SOURCE_TYPE_MISMATCH"):
                A.source(p, "ifc")

    def test_ifc_diff_uses_registered_upstream_module_and_semantic_relations(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            left, right = p / "before.ifc", p / "after.ifc"
            left.write_text("old"); right.write_text("new")
            with mock.patch.object(A, "invoke_module", return_value={"ok": True}) as invoke:
                result, paths = A.ifc_diff(type("Args", (), {
                    "a": str(left), "b": str(right), "output": str(p / "result.json")
                })())
            self.assertEqual(result, {"ok": True})
            self.assertEqual(paths, [left.resolve(), right.resolve()])
            self.assertEqual(invoke.call_args.args[0], "ifcdiff")
            self.assertEqual(invoke.call_args.args[1][2], "-r")

    def test_clash_set_is_source_pinned_and_has_no_shell_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "model.ifc"
            path.write_text("IFC")
            def inspect(module, arguments, output):
                self.assertEqual(module, "ifcclash")
                import json
                cfg = json.loads(Path(arguments[0]).read_text())
                self.assertEqual(cfg[0]["a"][0]["file"], str(path.resolve()))
                self.assertNotIn("b", cfg[0])
                self.assertEqual(cfg[0]["mode"], "intersection")
                self.assertEqual(cfg[0]["tolerance"], 0.001)
                self.assertFalse(cfg[0]["check_all"])
                return {"ok": True}
            with mock.patch.object(A, "invoke_module", side_effect=inspect):
                report, files = A.ifc_clash(type("Args", (), {
                    "a": str(path), "b": None, "output": str(path.parent / "out.json")
                })())
            self.assertEqual(files, [path.resolve()])
            self.assertEqual(report["ok"], True)

    def test_output_already_exists_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            inp = p / "source.pdf"; inp.write_text("%PDF-1.4")
            out = p / "existing.json"; out.write_text("KEEP")
            with mock.patch.object(A, "check_environment", return_value={"status": "READY"}):
                with mock.patch.dict(A.OPERATIONS, {"pdf-vectors": lambda args:
                        ({"mock": True}, [inp])}):
                    with self.assertRaisesRegex(ValueError, "OUTPUT_ALREADY_EXISTS"):
                        A.main(["pdf-vectors", "--a", str(inp), "--output", str(out)])
            self.assertEqual(out.read_text(), "KEEP")

    def test_explicit_output_is_provenance_tagged(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            inp = p / "source.dxf"; inp.write_text("DXF")
            out = p / "new.json"
            with mock.patch.object(A, "check_environment", return_value={"status": "READY"}):
                with mock.patch.dict(A.OPERATIONS, {"dxf-vectors": lambda args:
                        ({"facts": []}, [inp])}):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(A.main(["dxf-vectors", "--a", str(inp),
                                                 "--output", str(out)]), 0)
            import json
            proof = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(proof["nativeCalls"], 0)
            self.assertEqual(proof["modelWrites"], 0)
            self.assertEqual(proof["sources"][0]["sha256"], A.sha256(inp))
            self.assertEqual(proof["action"], "dxf-vectors")


    def test_existing_dynamic_router_local_provider_registration(self):
        class Router:
            def add_local_provider(self, namespace, contracts, handlers, source, dependencies):
                self.namespace = namespace
                self.contracts = contracts
                self.handlers = handlers
                self.dependencies = dependencies
            def contract_hash(self, key):
                return "exact-local-contract-sha"
            def review_policy(self, key, kind, impact, evidence):
                self.policies.append((key, kind, impact, evidence))
        router = Router()
        router.policies = []
        with mock.patch.object(Catalog, "verified_environment", return_value=("python", "script")):
            result = Catalog.register(router)
        self.assertEqual(router.namespace, "APAExternalReadOnly")
        self.assertEqual(len(router.contracts), 6)
        self.assertEqual(set(router.contracts), set(router.handlers))
        self.assertEqual(len(router.policies), 6)
        self.assertTrue(all(kind == impact == "READ_ONLY"
                            for _, kind, impact, _ in router.policies))
        self.assertEqual(result["modelWrites"], 0)

    def test_local_provider_dispatches_only_pinned_program_with_no_shell(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "evidence.json"
            result = {"schema": "APA_EXTERNAL_READONLY_EVIDENCE_V1",
                      "action": "ifc-diff", "modelWrites": 0, "nativeCalls": 0}
            output.write_text(json.dumps(result))
            with mock.patch.object(Catalog, "verified_environment",
                                   return_value=(Path("C:/venv/python.exe"), Path("C:/tools/adapter.py"))):
                with mock.patch.object(Catalog.subprocess, "run",
                                       return_value=type("Done", (), {
                                           "returncode": 0, "stdout": "", "stderr": ""
                                       })()) as dispatch:
                    actual = Catalog.call("ifc-diff",
                                          {"a": "before.ifc", "b": "after.ifc",
                                           "output": str(output)})
            self.assertEqual(actual["action"], "ifc-diff")
            self.assertFalse(dispatch.call_args.kwargs.get("shell", False))
            self.assertEqual(dispatch.call_args.args[0][2], "ifc-diff")


    def test_actual_apa_dynamic_commands_prepare_and_read(self):
        """Use original router implementation, not a test double for its guards."""
        from archicad_dynamic_commands import DynamicCommands
        router = DynamicCommands(dict(commands={}, common_schemas={}))
        with mock.patch.object(Catalog, "verified_environment",
                               return_value=("existing-python", "installed-adapter")):
            receipt = Catalog.register(router)
        command = "AddOn.APAExternalReadOnly.PDFVectors"
        params = {"a": "C:/fixture.pdf", "output": "C:/new-evidence.json"}
        ticket = router.prepare(command, params)
        self.assertEqual(ticket["effect"], "READ_ONLY")
        self.assertFalse(ticket["nativeWritePermission"])
        self.assertEqual(len(receipt["commands"]), 6)
        proof = {"schema": "APA_EXTERNAL_READONLY_EVIDENCE_V1",
                 "status": "SOURCE_ANALYSIS_ONLY_NOT_ENGINEERING_ACCEPTANCE",
                 "action": "pdf-vectors", "sources": [], "result": {},
                 "modelWrites": 0, "nativeCalls": 0}
        with mock.patch.object(Catalog, "call", return_value=proof) as dispatcher:
            response = router.read(None, ticket, reviewed_read_only=True)
        self.assertEqual(response, proof)
        dispatcher.assert_called_once_with("pdf-vectors", params)
        with self.assertRaisesRegex(ValueError, "SOURCE_REVIEWED_READ_ONLY_EFFECT_REQUIRED"):
            router.read(None, ticket, reviewed_read_only=False)


    def test_actual_activation_consumes_single_result_envelope(self):
        """Regression: local router's PDF/DXF evidence has one result key."""
        import json
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            exe = root / "venv" / "Scripts" / "python.exe"
            exe.parent.mkdir(parents=True)
            exe.touch()
            schema = "APA_EXTERNAL_READONLY_EVIDENCE_V1"
            def evidence(router, name, params):
                if name == "DXFVectors":
                    facts = {"sourceType": "DXF_RAW_MODELSPACE_FACTS_NOT_BIM",
                             "primitiveCount": 1,
                             "primitives": [{"type": "LINE"}]}
                    action = "dxf-vectors"
                elif name == "PDFVectors":
                    facts = {"sourceType": "VECTOR_PDF_FACTS_NOT_BIM",
                             "pages": [{"lineCount": 1}]}
                    action = "pdf-vectors"
                else:
                    raise AssertionError("Unexpected action " + name)
                return {"schema": schema, "action": action, "result": facts,
                        "nativeCalls": 0, "modelWrites": 0}
            with mock.patch.object(Activation, "EXT", root), (
                 mock.patch.object(Activation, "load_router", return_value=(object(), 21))), (
                 mock.patch.object(Activation, "register_installed", return_value={
                     "commands": ["a", "b", "c", "d", "e", "f"]})), (
                 mock.patch.object(Activation, "run_read", side_effect=evidence)), (
                 mock.patch.object(Activation.subprocess, "run",
                                   return_value=type("Done", (), {"returncode": 0})())), (
                 mock.patch.object(sys, "argv", ["apa_external_router_activation.py"])):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(Activation.main(), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], "READ_ONLY_ROUTE_PROBE_PASS")
            self.assertEqual(result["registeredCount"], 6)
            self.assertEqual(
                result["observedRuns"]["DXFVectors"]["status"],
                "EXECUTED_REAL_VENDOR_READ_ONLY_PASS")
            self.assertEqual(
                result["observedRuns"]["PDFVectors"]["status"],
                "EXECUTED_REAL_VENDOR_READ_ONLY_PASS")


    def test_upgrade_only_the_reviewed_clash_configuration(self):
        import hashlib
        import json
        with tempfile.TemporaryDirectory() as td:
            install = Path(td)
            (install / "venv" / "Scripts").mkdir(parents=True)
            (install / "venv" / "Scripts" / "python.exe").touch()
            latest = Upgrade.SRC.read_text(encoding="utf-8")
            self.assertIn(Upgrade.NEW, latest)
            baseline = latest.replace(Upgrade.NEW, Upgrade.OLD)
            (install / "apa_external_readonly.py").write_text(baseline, encoding="utf-8")
            (install / "apa_external_catalog.py").write_text("catalog", encoding="utf-8")
            (install / "requirements-external-readonly.txt").write_text("pins", encoding="utf-8")
            def sh(p):
                return hashlib.sha256(p.read_bytes()).hexdigest()
            receipt = {
                "schema": "APA_EXTERNAL_READONLY_INSTALL_V1",
                "status": "EXTERNAL_READONLY_INSTALLED_READY",
                "adapterSHA256": sh(install / "apa_external_readonly.py"),
                "catalogSHA256": sh(install / "apa_external_catalog.py"),
                "requirementsSHA256": sh(install / "requirements-external-readonly.txt")
            }
            (install / "installation.json").write_text(json.dumps(receipt))
            backup = install / "upgrade-ifcclash-intersection-v1"
            with mock.patch.object(Upgrade, "FOLDER", install), (
                 mock.patch.object(Upgrade, "BACKUP", backup)), (
                 mock.patch.object(Upgrade.subprocess, "run", return_value=type(
                    "Done", (), {"returncode": 0, "stderr": ""})())):
                result = Upgrade.upgrade()
                self.assertEqual(result["status"], "EXTERNAL_READONLY_IFCCLASH_ADAPTER_UPGRADED")
                self.assertEqual((install / "apa_external_readonly.py").read_text(), latest)
                self.assertEqual((backup / "apa_external_readonly.py.original").read_text(), baseline)
                updated = json.loads((install / "installation.json").read_text())
                self.assertEqual(updated["adapterSHA256"], sh(install / "apa_external_readonly.py"))
                with self.assertRaisesRegex(ValueError, "ALREADY_UPGRADED"):
                    Upgrade.review()

    def test_session_factory_reuses_original_router_without_second_writer(self):
        from archicad_dynamic_commands import DynamicCommands
        router = DynamicCommands({"commands": {}, "common_schemas": {}})
        def core_factory(schema, official, functional):
            self.assertEqual(schema, "schema.json")
            self.assertTrue(functional)
            return router
        with mock.patch.object(Session, "original_factory", return_value=core_factory), (
             mock.patch.object(Catalog, "verified_environment",
                               return_value=("python", "installed"))), (
             mock.patch.object(Session, "attach_existing",
                               side_effect=Catalog.register)):
            actual = Session.native_command_router("schema.json")
        self.assertIs(actual, router)
        self.assertEqual(len(actual.local_handlers), 6)
        self.assertTrue(all(actual.operation_kind(k) == "READ_ONLY"
                            for k in actual.local_handlers))


    def test_persistent_session_factory_installer_only_adds_isolated_files(self):
        """Original core and existing sidecar untouched, source JS provenance copied."""
        import json
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            destination = folder / "session-factory-v1"
            state = {
                "python": Path("C:/isolated/venv/Scripts/python.exe"),
                "schemaSHA256": PersistentFactory.sha(PersistentFactory.SCHEMA),
                "factorySHA256": PersistentFactory.sha(PersistentFactory.SOURCE),
                "provenanceSHA256": {
                    n: PersistentFactory.sha(PersistentFactory.SCHEMA_DIR / n)
                    for n in PersistentFactory.PROVENANCE
                },
                "adapterSHA256": PersistentFactory.EXPECTED_ADAPTER_SHA256,
                "catalogSHA256": "1" * 64,
            }
            probe = {
                "status": "FACTORY_SESSION_READ_ONLY_REGISTERED",
                "registered": ["AddOn.APAExternalReadOnly." + str(i) for i in range(6)],
                "nativeCalls": 0,
                "modelWrites": 0,
                "autoRegisteredWithinFactorySessions": True,
            }
            done = type("Done", (), {
                "returncode": 0, "stdout": json.dumps(probe), "stderr": ""
            })()
            with mock.patch.object(PersistentFactory, "DEST", destination), (
                 mock.patch.object(PersistentFactory, "preflight", return_value=state)), (
                 mock.patch.object(PersistentFactory.subprocess, "run", return_value=done)):
                result = PersistentFactory.install()
                self.assertEqual(result["status"], "SESSION_FACTORY_INSTALLED_READY")
                self.assertFalse(result["originalCorePatched"])
                self.assertFalse(result["existingProcessesModified"])
                self.assertEqual((destination / "tapir-scene-live.json").read_bytes(),
                                 PersistentFactory.SCHEMA.read_bytes())
                for file in PersistentFactory.PROVENANCE:
                    self.assertEqual((destination / file).read_bytes(),
                                     (PersistentFactory.SCHEMA_DIR / file).read_bytes())
                receipt = json.loads(
                    (destination / "session-factory-install.json").read_text())
                self.assertEqual(receipt["provenanceSHA256"], state["provenanceSHA256"])
                with self.assertRaisesRegex(ValueError, "SESSION_FACTORY_EXISTS"):
                    PersistentFactory.install()


    def test_original_apa_router_accepts_pinned_tapir_js_provenance(self):
        """Verify the real original factory, not just load_catalog(), on exact JS."""
        source_root = Path(__file__).resolve().parents[1]
        snapshot = source_root / "schemas/tapir-live-1.5.10/tapir-scene-live.json"
        with mock.patch.object(Session, "STABLE", source_root):
            original = Session.original_factory()
            router = original(snapshot, None, False)
        self.assertGreaterEqual(len(router.catalog["commands"]), 260)
        self.assertTrue(router.fingerprint)


if __name__ == "__main__":
    unittest.main()
