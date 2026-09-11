"""
Unit tests for data models and serialization in Auto Clicker Pro.
"""

import unittest
from models import ActionPoint, ActionType

class TestActionPoint(unittest.TestCase):
    def test_default_initialization(self):
        p = ActionPoint()
        self.assertEqual(p.action, ActionType.CLICK)
        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)
        self.assertEqual(p.count, 1)

    def test_to_dict_and_from_dict(self):
        original = ActionPoint(
            action=ActionType.DRAG,
            name="Test Drag",
            x=150,
            y=250,
            drag_x=400,
            drag_y=500,
            hold=450,
            count=2,
            delay_after=80
        )
        d = original.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["action"], "drag")
        self.assertEqual(d["x"], 150)
        self.assertEqual(d["drag_x"], 400)

        restored = ActionPoint.from_dict(d)
        self.assertEqual(restored.action, original.action)
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.x, original.x)
        self.assertEqual(restored.drag_x, original.drag_x)
        self.assertEqual(restored.hold, original.hold)
        self.assertEqual(restored.count, original.count)

    def test_dict_access_compatibility(self):
        p = ActionPoint(action=ActionType.WAIT, delay=750)
        # Test item access
        self.assertEqual(p["action"], "wait")
        self.assertEqual(p["delay"], 750)
        # Test get() method
        self.assertEqual(p.get("delay"), 750)
        self.assertEqual(p.get("non_existent", 42), 42)
        # Test item mutation
        p["delay"] = 1000
        self.assertEqual(p.delay, 1000)

if __name__ == "__main__":
    unittest.main()
