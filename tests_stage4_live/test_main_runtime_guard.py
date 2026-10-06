import subprocess
import unittest
from unittest.mock import patch

from closed_loop.live_wall import MAIN_BASELINE, PROTECTED_MAIN_PATHS, main_runtime_guard


class MainRuntimeGuardTests(unittest.TestCase):
    def test_unrelated_main_change_does_not_fail_stage4(self):
        with patch('closed_loop.live_wall.subprocess.run') as run, \
             patch('closed_loop.live_wall.subprocess.check_output',
                   side_effect=['d5695f435a5841d39f0fe69a6424cccc1c8d0a4c\n', '']):
            result = main_runtime_guard()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['baselineMain'], MAIN_BASELINE)
        self.assertEqual(result['changedProtectedPaths'], [])
        run.assert_called_once()
        self.assertIn('main', run.call_args.args[0])

    def test_protected_main_change_fails_stage4(self):
        changed = 'closed_loop/orchestrator.py\nscripts/archicad_executor.py\n'
        with patch('closed_loop.live_wall.subprocess.run'), \
             patch('closed_loop.live_wall.subprocess.check_output',
                   side_effect=['deadbeef\n', changed]):
            result = main_runtime_guard()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(
            result['changedProtectedPaths'],
            ['closed_loop/orchestrator.py', 'scripts/archicad_executor.py'])
        self.assertIn('closed_loop', PROTECTED_MAIN_PATHS)
        self.assertIn('scripts', PROTECTED_MAIN_PATHS)


if __name__ == '__main__':
    unittest.main()
