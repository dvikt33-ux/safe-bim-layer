"""Вариант fake_backend: set_property_value молча ничего не пишет (класс E3)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_backend import FakeBackend, MODEL


class SilentNoopBackend(FakeBackend):
    name = "fake_noop"

    def set_property_value(self, guid, ref, value):
        return None   # 200 OK, значение не записано


BACKEND = SilentNoopBackend
