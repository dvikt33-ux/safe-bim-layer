"""Вариант: в модели уже есть наследие BX:PROBE: от прерванного прогона."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_backend import FakeBackend, MODEL

MODEL["props"]["G-0002"]["General_ElementID"] = "BX:PROBE:deadbeef"


class LeftoverBackend(FakeBackend):
    name = "fake_leftover"


BACKEND = LeftoverBackend
