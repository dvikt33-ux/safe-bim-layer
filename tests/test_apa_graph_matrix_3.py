"""Quarter 3: 64 independent DAGs and 64 independent forced cycles."""
import pytest
from apa_graph_matrix_helper import check_acyclic, check_cycle

@pytest.mark.parametrize("case", range(128, 192))
def test_dag_topological_order_and_purity(case):
    check_acyclic((case * 37) % 1024)

@pytest.mark.parametrize("case", range(128, 192))
def test_force_three_node_cycle_detection(case):
    check_cycle((case * 37) % 1024)
