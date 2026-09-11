"""
Unit tests for Profile persistence and backward compatibility.
"""

import os
import json
import tempfile
import unittest
from models import ActionPoint, ActionType
from profiles_manager import ProfilesManager

class TestProfilesManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_save_and_load_roundtrip(self):
        sample_data = {
            "points": [
                ActionPoint(action=ActionType.CLICK, x=100, y=200, type="Right", hold=100),
                ActionPoint(action=ActionType.WAIT, delay=500),
                ActionPoint(action=ActionType.KEY, key="ctrl+s")
            ],
            "random": 15,
            "pos_random": 3,
            "cycles": 5,
            "infinite": False,
            "speed": 1.5,
            "start_hotkey": "f6",
            "pause_hotkey": "f7",
            "stop_hotkey": "f8",
            "record_start_hotkey": "f9",
            "record_stop_hotkey": "f10",
            "start_enabled": True,
            "pause_enabled": True,
            "stop_enabled": True,
            "record_start_enabled": False,
            "record_stop_enabled": False,
            "always_on_top": True,
        }

        ProfilesManager.save_profile_to_file(self.temp_file.name, sample_data)
        loaded = ProfilesManager.load_profile_from_file(self.temp_file.name)

        self.assertEqual(len(loaded["points"]), 3)
        self.assertEqual(loaded["points"][0].action, ActionType.CLICK)
        self.assertEqual(loaded["points"][0].x, 100)
        self.assertEqual(loaded["points"][1].action, ActionType.WAIT)
        self.assertEqual(loaded["points"][1].delay, 500)
        self.assertEqual(loaded["points"][2].action, ActionType.KEY)
        self.assertEqual(loaded["points"][2].key, "ctrl+s")

        self.assertEqual(loaded["random"], 15)
        self.assertEqual(loaded["pos_random"], 3)
        self.assertEqual(loaded["cycles"], 5)
        self.assertEqual(loaded["speed"], 1.5)
        self.assertEqual(loaded["start_hotkey"], "f6")
        self.assertTrue(loaded["always_on_top"])

    def test_legacy_profile_backward_compatibility(self):
        # A profile created by earlier versions using raw dicts
        legacy_json = {
            "points": [
                {"action": "click", "x": 300, "y": 400, "type": "Left", "hold": 50, "count": 1, "delay_after": 100},
                {"action": "wait", "delay": 250}
            ],
            "random": 0,
            "pos_random": 0,
            "cycles": 1,
            "infinite": False,
            "speed": 1.0,
            "start_hotkey": "f1",
            "pause_hotkey": "f2",
            "stop_hotkey": "f3",
            "record_start_hotkey": "f4",
            "record_stop_hotkey": "f5",
            "start_enabled": True,
            "pause_enabled": True,
            "stop_enabled": True,
            "record_start_enabled": True,
            "record_stop_enabled": True,
            "always_on_top": False
        }

        with open(self.temp_file.name, "w", encoding="utf-8") as f:
            json.dump(legacy_json, f)

        loaded = ProfilesManager.load_profile_from_file(self.temp_file.name)
        self.assertEqual(len(loaded["points"]), 2)
        self.assertIsInstance(loaded["points"][0], ActionPoint)
        self.assertEqual(loaded["points"][0].x, 300)
        self.assertEqual(loaded["points"][0].y, 400)
        self.assertEqual(loaded["points"][1].delay, 250)

if __name__ == "__main__":
    unittest.main()
