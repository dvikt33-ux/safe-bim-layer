#!/usr/bin/env python3
"""Прогон всех наборов тестов. Возвращает 1, если что-то упало."""
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
sys.path.insert(0, os.path.join(root, "reference"))
sys.path.insert(0, root)

import tests.test_p0 as t0
import tests.test_probe as tp
import tests.test_t2_probe as tt2
import tests.test_t2_connections as tt2c
import tests.test_t3_dependency as tt3
import tests.test_t3_reconcile as tt3r
import tests.test_t4_timeout as tt4
import tests.test_t5_kill as tt5

failed = 0
for mod in (t0, tp, tt2, tt2c, tt3, tt3r, tt4, tt5):
    print(f"\n=== {mod.__name__}")
    for name, fn in mod.TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception:
            failed += 1
            print(f"  FAIL  {name}")
            import traceback
            traceback.print_exc()
print(f"\n{'FAILED' if failed else 'OK'}: {failed} failure(s)")
raise SystemExit(1 if failed else 0)
