"""
Integration tests for popup invocations and screen capture listeners.
"""

import unittest
import tkinter as tk
from main import AutoClickerApp
from models import ActionPoint, ActionType

class TestPopupsIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.app = AutoClickerApp(cls.root)
        cls.root.update()

    @classmethod
    def tearDownClass(cls):
        cls.app.exit_app()

    def test_selected_index_property(self):
        self.assertIsNone(self.app.selected_index)
        self.app.selected_index = 2
        self.assertEqual(self.app.list_manager.selected_index, 2)
        self.app.selected_index = None

    def test_clipboard_property(self):
        self.assertIsNone(self.app.clipboard_point)
        self.app.clipboard_point = {"action": "click"}
        self.assertEqual(self.app.list_manager.clipboard_point, {"action": "click"})
        self.app.clipboard_point = None

    def test_start_add_point_creates_listener(self):
        self.app.start_add_point("click")
        self.assertIsNotNone(self.app.click_listener)
        self.assertTrue(self.app.click_listener.is_alive())

        # Cleanup listener
        if self.app.click_listener and self.app.click_listener.is_alive():
            self.app.click_listener.stop()
        self.app.click_listener = None
        self.app.restore_after_capture()

    def test_edit_popup_with_point(self):
        # Add sample point
        p = ActionPoint(action=ActionType.CLICK, x=100, y=150)
        self.app.points.append(p)
        self.app.selected_index = 0
        # Call open_edit_popup without error
        try:
            # open_edit_popup opens a toplevel window
            self.app.open_edit_popup()
        finally:
            self.app.clear_previews()
            self.app.points.clear()
            self.app.selected_index = None

if __name__ == "__main__":
    unittest.main()
