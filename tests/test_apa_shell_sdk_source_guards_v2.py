"""Real checked-in Shell C++ source review gates only: NOT a native build or LIVE test."""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "archicad-addon/Sources/NativeExtendedModules.cpp"
ASSEMBLY = ROOT / "archicad-addon/Sources/NativeAssemblyCommands.inc"
GUARDS = [
    "case API_ExtrudedShellID:",
    "case API_RevolvedShellID:",
    "case API_RuledShellID:",
    "ShellClassParameters(e.shell)",
    "row.Add(\"shellContourCountExpected\",n)",
    "row.Add(\"shellContourCountAllocated\",static_cast<Int32>(allocated))",
    "if(e.shell.numHoles>4096)",
    "if(static_cast<GSSize>(n)>allocated)",
    "GetAttributeIndex(edge.sideMaterial.value)",
    "bodyFlagIndexAuthority",
    "RAW_NATIVE_ALLOCATION_INDEX_NO_REINDEXING",
    "planeTransform",
    "edgeData",
    "APIERR_BADPARS,\"Shell contour allocation shorter than element metadata\"",
    "NATIVE_PARAMETER_GEOMETRY_NOT_RESULTANT_BREP",
    "case API_ShellID",
]


@pytest.mark.parametrize("guard", GUARDS)
def test_shell_cpp_checked_in_required_source_guards(guard):
    source = CPP.read_text(encoding="utf8")
    assert source.count(guard) >= 1
    assert guard not in source.replace(guard, "", 1)
    assert CPP.is_file()
    assert ASSEMBLY.is_file()
    assert "API_ShellID" in source
