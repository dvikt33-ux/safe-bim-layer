from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import apa_archicad_startup as startup
from apa_ac29_save_isolation import write_new_json
from apa_release import sha256


class StartupDiagnosticsTests(unittest.TestCase):
    def test_owned_modal_blocks_probes_and_hidden_or_other_owner_does_not(self):
        recovery = dict(ownerPid=31, windowClass="DGModalDlgClass", visible=True,
                        enabled=True, caption="Восстановление Проекта Archicad")
        row = startup.inspect_project(None, 31, [19725], [recovery], self.unexpected_api)
        self.assertEqual(row["status"], "WAITING_FOR_OPERATOR")
        self.assertEqual(row["dialogs"][0]["kind"], "POSSIBLE_PROJECT_RECOVERY")
        self.assertEqual(row["nativeModelWrites"], 0)
        self.assertFalse(startup.pending_window([dict(recovery, visible=False),
                                                 dict(recovery, ownerPid=32)], 31))

    def test_only_exact_pln_archicad_and_loaded_addon_can_be_verified(self):
        project = Path("exact-test.pln")
        binding = SimpleNamespace(project=project, pinned_runtime=("revision", "build"))
        pinned = dict(contract="APA_NATIVE_RUNTIME_IDENTITY_V1", sdkMajor=29,
                      sourceRevision="revision", buildIdentity="build", nativeModelWrites=0)
        seen = []

        def read(port, command):
            seen.append((port, command))
            return {
                "GetProjectInfo": dict(projectPath=str(project) if port != 19723 else "other.pln",
                                       projectName=project.stem, isUntitled=False, isTeamwork=False),
                "API.GetProductInfo": dict(version=29, buildNumber=5101),
                "GetAddOnVersion": {"version": "1.5.10"},
                "GetAPARuntimeInfoV1": dict(pinned, buildIdentity="other") if port == 19724 else pinned,
            }[command]

        row = startup.inspect_project(binding, 31, [19723, 19724], [], read)
        self.assertEqual(row["status"], "API_LISTENING")
        self.assertEqual([issue["phase"] for issue in row["issues"]], ["PROJECT_IDENTITY", "RUNTIME_IDENTITY"])
        self.assertEqual([cmd for port, cmd in seen if port == 19723], ["GetProjectInfo"])
        row = startup.inspect_project(binding, 31, [19725], [], read)
        self.assertEqual(row["status"], "PROJECT_IDENTITY_VERIFIED")
        self.assertEqual(row["port"], 19725)

    def test_starter_child_tracked_without_substituting_another_instance(self):
        tracked = {10: "2026-11-13T10:00:00"}
        old = dict(ProcessId=11, ParentProcessId=10, startedAt="2026-11-13T09:00:00")
        child = dict(ProcessId=12, ParentProcessId=10, startedAt="2026-11-13T10:00:01")
        other = dict(ProcessId=13, ParentProcessId=20, startedAt="2026-11-13T09:00:00")
        self.assertEqual(startup.followed_processes([old, other, child], tracked), [child])

    def test_resume_keeps_the_original_modal_receipt_and_exact_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            source = folder / "saved.pln"
            source.write_bytes(b"saved model fixture")
            copy = folder / "model" / source.name
            copy.parent.mkdir()
            copy.write_bytes(source.read_bytes())
            digest = sha256(source)
            started = dict(ProcessId=42, startedAt="2026-11-14T10:00:00Z")
            write_new_json(folder / "launch-intent.json", dict(project=str(copy), sha256=digest))
            path = folder / "startup.json"
            write_new_json(path, dict(status="WAITING_FOR_OPERATOR", project=str(copy),
                originalProject=str(source), projectSha256=digest, plnBytesUnchanged=True,
                nativeModelWrites=0, events=[dict(status="WAITING_FOR_OPERATOR", pid=42, process=started)]))
            prior = sha256(path)
            self.assertEqual(startup.resume_session(folder, source, digest, 42), (copy, started, prior))
            self.assertEqual(sha256(path), prior)
            with self.assertRaisesRegex(ValueError, "RESUME_PID_NOT_PROVEN"):
                startup.resume_session(folder, source, digest, 41)
            copy.write_bytes(b"other bytes")
            with self.assertRaisesRegex(ValueError, "RESUME_SOURCE_DRIFT"):
                startup.resume_session(folder, source, digest, 42)

    def unexpected_api(self, *_):
        self.fail("A pending recovery dialog must prevent API probes")
