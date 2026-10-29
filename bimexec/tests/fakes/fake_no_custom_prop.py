"""Вариант: user-defined property НЕ существует (ожидаемый реальный случай)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_tapir_shape import FakeTapirShape, MODEL


class NoCustomPropBackend(FakeTapirShape):
    name = "tapir"

    def resolve_property_id(self, ref):
        if ref.get("kind") == "user":
            raise BackendError("no id for address 'BIMEXEC/BIMEXEC_MARKER'")
        return super().resolve_property_id(ref)

    def get_property_values(self, ref, guids):
        if ref.get("kind") == "user":
            raise BackendError("no id for address 'BIMEXEC/BIMEXEC_MARKER'")
        return super().get_property_values(ref, guids)


from backends import BackendError  # noqa: E402
BACKEND = NoCustomPropBackend
