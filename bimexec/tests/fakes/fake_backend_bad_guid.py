"""Вариант: GetElementsByType отвечает, но GUID пустые.

Класс дефекта: «вызов прошёл, список непустой, работать не с чем».
Раньше T0A засчитывал это как подтверждённую способность.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "probes")))
from fake_tapir_shape import FakeTapirShape  # noqa: E402


class BadGuidBackend(FakeTapirShape):
    name = "tapir"

    def elements_by_type(self, element_type):
        return ["", "   "]

    def all_elements(self):
        return ["", "   "]


BACKEND = BadGuidBackend
