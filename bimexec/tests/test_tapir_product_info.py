"""Regression tests for the live Archicad GetProductInfo tuple contract."""
from __future__ import annotations

import os
import sys
import traceback

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
if root not in sys.path:
    sys.path.insert(0, root)

from probes.backends import TapirBackend


TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


@test
def product_info_tuple_maps_version_and_build():
    backend = TapirBackend()
    backend._official = lambda name: lambda: (29, 3000, "RUS")

    assert backend._product_info("version", "archicadVersion") == "29"
    assert backend._product_info("build", "buildNumber") == "3000"


@test
def project_info_uses_live_product_tuple_without_touching_project_identity():
    backend = TapirBackend()
    project = {
        "projectPath": r"C:\Users\Example\Project.pln",
        "projectName": "Project",
        "isUntitled": False,
        "isTeamwork": False,
    }
    backend._tapir = lambda name: lambda params=None: dict(project)
    backend._official = lambda name: lambda: (29, 3000, "RUS")

    info = backend.project_info()

    assert info["project_path"] == project["projectPath"]
    assert info["project_name"] == "Project"
    assert info["is_untitled"] is False
    assert info["is_teamwork"] is False
    assert info["archicad_version"] == "29"
    assert info["archicad_build"] == "3000"


@test
def missing_official_product_info_remains_nonfatal():
    backend = TapirBackend()
    project = {
        "projectPath": r"C:\Users\Example\Project.pln",
        "projectName": "Project",
        "isUntitled": False,
        "isTeamwork": False,
    }
    backend._tapir = lambda name: lambda params=None: dict(project)

    def missing(_name):
        raise AttributeError("GetProductInfo unavailable")

    backend._official = missing
    info = backend.project_info()

    assert info["archicad_version"] == ""
    assert info["archicad_build"] == ""
    assert info["project_path"] == project["projectPath"]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception:
            failed += 1
            print(f"  FAIL  {name}")
            traceback.print_exc()
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
