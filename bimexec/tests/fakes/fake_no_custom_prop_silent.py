"""Вариант: свойства нет, но get_property_values НЕ падает — возвращает пустые
значения. Именно тот случай, который раньше ложно давал read_custom_property=OK.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "probes")))
from fake_tapir_shape import FakeTapirShape  # noqa: E402
from backends import BackendError  # noqa: E402


class SilentMissingPropBackend(FakeTapirShape):
    name = "tapir"

    def resolve_property_id(self, ref):
        if ref.get("kind") == "user":
            raise BackendError("no id for address 'BIMEXEC/BIMEXEC_MARKER'")
        return super().resolve_property_id(ref)

    def get_property_values(self, ref, guids):
        if ref.get("kind") == "user":
            return {g: None for g in guids}      # 200 OK, значений нет
        return super().get_property_values(ref, guids)


BACKEND = SilentMissingPropBackend
