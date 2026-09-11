"""
Unit tests for ActionsEngine jitter math, speed factors, and legacy AutoClicker alias.
"""

import unittest
from actions_engine import ActionsEngine
from hotkey_manager import HotkeyManager
from main import AutoClicker, AutoClickerApp

class DummyVar:
    def __init__(self, val):
        self._val = val
    def get(self):
        return self._val

class DummyApp:
    def __init__(self):
        self.speed_var = DummyVar(2.5)
        self.random_var = DummyVar(10)
        self.pos_random_var = DummyVar(5)
        self.rep_var = DummyVar(3)
        self.infinite = DummyVar(False)
        self.points = []

class TestActionsEngine(unittest.TestCase):
    def setUp(self):
        self.app = DummyApp()
        self.engine = ActionsEngine(self.app)

    def test_legacy_alias(self):
        self.assertIs(AutoClicker, AutoClickerApp)

    def test_speed_factor(self):
        self.assertEqual(self.engine.get_speed_factor(), 2.5)
        self.app.speed_var = DummyVar(99.0)
        self.assertEqual(self.engine.get_speed_factor(), 20.0)  # max clamp
        self.app.speed_var = DummyVar(-5.0)
        self.assertEqual(self.engine.get_speed_factor(), 0.1)   # min clamp

    def test_apply_pos_random(self):
        # 0 jitter -> exact same coordinate
        x, y = self.engine.apply_pos_random(100, 200, 0)
        self.assertEqual(x, 100)
        self.assertEqual(y, 200)

        # with jitter -> within bounds
        for _ in range(50):
            rx, ry = self.engine.apply_pos_random(100, 200, 10)
            self.assertTrue(90 <= rx <= 110)
            self.assertTrue(190 <= ry <= 210)

    def test_hotkey_manager_defaults(self):
        hm = HotkeyManager(is_focus_on_input=lambda: False)
        all_hk = hm.get_all_hotkeys()
        self.assertEqual(all_hk["start"], "f1")
        self.assertEqual(all_hk["pause"], "f2")
        self.assertEqual(all_hk["stop"], "f3")
        self.assertEqual(all_hk["record_start"], "f4")
        self.assertEqual(all_hk["record_stop"], "f5")

if __name__ == "__main__":
    unittest.main()
