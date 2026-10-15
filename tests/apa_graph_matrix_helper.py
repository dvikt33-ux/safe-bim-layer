"""Independent deterministic topology checks against the production BIM graph planner."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_bim_graph as G

IDS = tuple("node_" + str(i) for i in range(5))
PAIRS = tuple((i, j) for i in range(5) for j in range(i + 1, 5))

def dependencies(mask):
    """Enumerate a distinct directed acyclic graph from a ten-edge bit mask."""
    assert 0 <= mask < 1024
    deps = {n: set() for n in IDS}
    for bit, (a, b) in enumerate(PAIRS):
        if mask & (1 << bit):
            deps[IDS[b]].add(IDS[a])
    return deps

def check_acyclic(mask):
    deps = dependencies(mask)
    before = {k: frozenset(v) for k, v in deps.items()}
    order = G._topo(IDS, deps)
    assert order is not None
    assert len(order) == len(IDS) and set(order) == set(IDS)
    positions = {node: i for i, node in enumerate(order)}
    assert all(positions[parent] < positions[child]
               for child, parents in deps.items() for parent in parents)
    assert G._topo(IDS, deps) == order  # Stable ordering for identical source.
    assert before == {k: frozenset(v) for k, v in deps.items()}  # Pure planner.

def check_cycle(mask):
    deps = dependencies(mask)
    # Forced 3-node cycle, plus independently varying unrelated dependencies.
    deps[IDS[1]].add(IDS[0])
    deps[IDS[2]].add(IDS[1])
    deps[IDS[0]].add(IDS[2])
    assert G._topo(IDS, deps) is None
