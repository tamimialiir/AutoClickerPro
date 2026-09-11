"""
Unit tests for visual custom widgets (ToggleSwitch, ActionCardsView, ActionCard)
and action mute execution filtering.
"""

import unittest
import tkinter as tk
from widgets import ToggleSwitch, ActionCardsView, ActionCard
from models import ActionPoint, ActionType
from actions_engine import ActionsEngine
from theme import Theme

class TestToggleSwitch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_toggle_switch_initialization(self):
        var = tk.BooleanVar(value=False)
        called = []
        sw = ToggleSwitch(self.root, variable=var, command=lambda: called.append(True))

        self.assertFalse(var.get())
        self.assertEqual(sw.state, "normal")

        # Simulate click
        sw._on_click()
        self.assertTrue(var.get())
        self.assertEqual(len(called), 1)

        # Click again to toggle off
        sw._on_click()
        self.assertFalse(var.get())
        self.assertEqual(len(called), 2)

    def test_toggle_switch_disabled_state(self):
        var = tk.BooleanVar(value=True)
        called = []
        sw = ToggleSwitch(self.root, variable=var, command=lambda: called.append(True), state="disabled")

        # In disabled state, click should NOT toggle
        sw._on_click()
        self.assertTrue(var.get())
        self.assertEqual(len(called), 0)

        # Enable it
        sw.config(state="normal")
        self.assertEqual(sw.state, "normal")
        sw._on_click()
        self.assertFalse(var.get())
        self.assertEqual(len(called), 1)

    def test_toggle_switch_high_contrast_colors(self):
        var = tk.BooleanVar(value=True)
        sw = ToggleSwitch(self.root, variable=var)
        self.assertEqual(sw.active_color, "#4e6d94")
        self.assertEqual(sw.thumb_color, "#ffffff")
        self.assertEqual(sw.bg_color, "#252738")

    def test_toggle_switch_thumb_dimensions_equal_on_off(self):
        var = tk.BooleanVar(value=False)
        sw = ToggleSwitch(self.root, variable=var, width=32, height=16)
        sw.draw()
        items = sw.find_all()
        thumb_off = items[-1]
        bbox_off = sw.bbox(thumb_off)
        width_off = bbox_off[2] - bbox_off[0]
        height_off = bbox_off[3] - bbox_off[1]

        # Switch to ON
        var.set(True)
        items_on = sw.find_all()
        thumb_on = items_on[-1]
        bbox_on = sw.bbox(thumb_on)
        width_on = bbox_on[2] - bbox_on[0]
        height_on = bbox_on[3] - bbox_on[1]

        # Thumb dimensions must be mathematically and visually identical between ON and OFF
        self.assertEqual(width_off, width_on)
        self.assertEqual(height_off, height_on)


class TestActionCardsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_action_cards_empty_and_render(self):
        view = ActionCardsView(self.root)
        view.render([])
        # Should render 1 child (the empty state box)
        self.assertEqual(len(view.inner_frame.winfo_children()), 1)

        # Render points
        points = [
            ActionPoint(action=ActionType.CLICK, x=100, y=200, type="Left"),
            ActionPoint(action=ActionType.WAIT, delay=750, enabled=False),
        ]
        view.render(points)
        self.assertEqual(len(view.cards), 2)
        self.assertIsInstance(view.cards[0], ActionCard)
        self.assertIsInstance(view.cards[1], ActionCard)

        # Selection
        view.select(0)
        self.assertEqual(view.selected_index, 0)
        self.assertTrue(view.cards[0].is_selected)
        self.assertFalse(view.cards[1].is_selected)

        # Highlighting
        view.highlight_current(1)
        self.assertEqual(view.highlighted_index, 1)
        self.assertTrue(view.cards[1].is_active_step)

        view.clear_highlight()
        self.assertIsNone(view.highlighted_index)
        self.assertFalse(view.cards[1].is_active_step)

    def test_action_card_double_click_triggers_edit(self):
        selected = []
        edited = []
        points = [ActionPoint(action=ActionType.CLICK, x=50, y=50)]

        view = ActionCardsView(
            self.root,
            on_select=lambda idx: selected.append(idx),
            on_edit=lambda idx: edited.append(idx)
        )
        view.render(points)
        card = view.cards[0]

        # Trigger double click handler
        card._on_double_click_handler()
        self.assertEqual(selected, [0])
        self.assertEqual(edited, [0])

    def test_action_card_key_title_and_pill_no_redundancy(self):
        p = ActionPoint(action=ActionType.KEY, key="dd")
        view = ActionCardsView(self.root)
        view.render([p])

        card = view.cards[0]
        # Title must be just "Key", not "Key 'dd'"
        self.assertTrue(card.title_label.cget("text").strip().endswith("Key"))
        self.assertNotIn("'dd'", card.title_label.cget("text"))
        # Parameter pill must contain "'dd'"
        pills = [w.cget("text") for w in card.badges_frame.winfo_children() if isinstance(w, tk.Label)]
        self.assertIn("'dd'", pills)

    def test_action_card_long_name_truncation(self):
        long_name = "SuperUltraMegaLongCustomActionNameThatExceedsLimit"
        p = ActionPoint(action=ActionType.CLICK, x=100, y=200, name=long_name)
        view = ActionCardsView(self.root)
        view.render([p])

        card = view.cards[0]
        self.assertIn("...", card.title_label.cget("text"))
        self.assertLess(len(card.title_label.cget("text")), len(long_name))

    def test_action_card_long_key_truncation_and_right_controls(self):
        long_key = "ajbgdngkpsnppffpnnfpsnpfpbfsbgjbnsjkf;bnskfb;pksfb;spfnlf!"
        p = ActionPoint(action=ActionType.KEY, key=long_key)
        view = ActionCardsView(self.root)
        view.render([p])

        card = view.cards[0]
        # Title remains clean "Key" without key value
        self.assertTrue(card.title_label.cget("text").strip().endswith("Key"))
        self.assertNotIn(long_key, card.title_label.cget("text"))
        # Pill truncates long key string
        pills = [w.cget("text") for w in card.badges_frame.winfo_children() if isinstance(w, tk.Label)]
        self.assertTrue(any("..." in p_text for p_text in pills))

        card.update_idletasks()
        self.assertTrue(card.right_ctrls.winfo_ismapped())
        self.assertTrue(card.enable_switch.winfo_ismapped())
        self.assertTrue(card.del_btn.winfo_ismapped())

    def test_scroll_action_amount_pill(self):
        p = ActionPoint(action=ActionType.SCROLL, x=150, y=250, dy=-5)
        view = ActionCardsView(self.root)
        view.render([p])

        card = view.cards[0]
        self.assertIn("Scroll DOWN", card.title_label.cget("text"))
        pills = [w.cget("text") for w in card.badges_frame.winfo_children() if isinstance(w, tk.Label)]
        self.assertIn("Amount: 5", pills)
        self.assertNotIn("dy:", "".join(pills))

    def test_action_cards_live_drag_and_drop_reordering(self):
        points = [
            ActionPoint(action=ActionType.CLICK, x=10, y=10, name="Point 1"),
            ActionPoint(action=ActionType.CLICK, x=20, y=20, name="Point 2"),
            ActionPoint(action=ActionType.CLICK, x=30, y=30, name="Point 3"),
        ]
        reordered = []
        view = ActionCardsView(self.root, on_reorder=lambda: reordered.append(True))
        view.render(points)

        # Force geometry update
        self.root.update_idletasks()

        # Simulate dragging card 0 down into card 2 position
        card2_y = view.cards[2].winfo_rooty() + 5
        view.handle_card_drag(dragged_index=0, mouse_y_root=card2_y)

        # Verify points list order changed
        self.assertEqual(points[0].name, "Point 2")
        self.assertEqual(points[1].name, "Point 3")
        self.assertEqual(points[2].name, "Point 1")

        # Verify no card titles have '{' or 'None' (regression test for drag & drop tuple bug)
        for card in view.cards:
            title = card.title_label.cget("text")
            self.assertNotIn("{", title)
            self.assertNotIn("None", title)

        # Finish drag
        view.finish_card_drag()
        self.assertEqual(len(reordered), 1)

    def test_action_cards_drag_stability_no_repeated_swapping(self):
        """Verify that holding mouse over target slot across many motion events does NOT cause jitter or oscillation."""
        points = [
            ActionPoint(action=ActionType.CLICK, x=10, y=10, name="Alpha"),
            ActionPoint(action=ActionType.CLICK, x=20, y=20, name="Beta"),
            ActionPoint(action=ActionType.CLICK, x=30, y=30, name="Gamma"),
        ]
        view = ActionCardsView(self.root)
        view.render(points)
        self.root.update_idletasks()

        # Start drag at card 0 (Alpha)
        view.start_card_drag(initial_index=0)
        card1_mid = view.cards[1].winfo_rooty() + (view.cards[1].winfo_height() // 2) + 2

        # Send 25 consecutive motion events over card 1's position
        for _ in range(25):
            view.handle_card_drag(dragged_index=0, mouse_y_root=card1_mid)
            # Order MUST remain [Beta, Alpha, Gamma] and NOT ping-pong back to [Alpha, Beta, Gamma]!
            self.assertEqual(points[0].name, "Beta")
            self.assertEqual(points[1].name, "Alpha")
            self.assertEqual(points[2].name, "Gamma")

        # Finish drag
        view.finish_card_drag()
        self.assertEqual(points[0].name, "Beta")
        self.assertEqual(points[1].name, "Alpha")
        self.assertEqual(points[2].name, "Gamma")

    def test_see_does_not_jump_when_already_visible(self):
        """Verify that selecting an already visible card does not scroll or jump the viewport."""
        self.root.geometry("400x500")
        view = ActionCardsView(self.root)
        view.pack(fill="both", expand=True)
        points = [ActionPoint(action=ActionType.CLICK, x=i*10, y=i*10, name=f"P{i}") for i in range(15)]
        view.render(points)
        self.root.update()

        # Initial scroll position at top
        initial_yview = view.canvas.yview()

        # Selecting already visible card (e.g. index 1) must NOT change yview
        view.select(1)
        self.assertEqual(view.canvas.yview(), initial_yview)
        view.destroy()


class DummyApp:
    def __init__(self, points, root):
        self.points = points
        self.root = root
        self.infinite = tk.BooleanVar(value=False)
        self.speed_var = tk.DoubleVar(value=20.0)
        self.executed_actions = []

        class DummyListManager:
            def highlight_current(self, i):
                pass
            def clear_highlight(self):
                pass

        class DummyLabel:
            def config(self, **kwargs):
                pass

        self.list_manager = DummyListManager()
        self.progress_label = DummyLabel()
        self.status_label = DummyLabel()

    def set_ui_lock_state(self, s):
        pass

class TestActionMuting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_muted_actions_are_skipped(self):
        points = [
            ActionPoint(action=ActionType.CLICK, x=10, y=10, enabled=True),
            ActionPoint(action=ActionType.WAIT, delay=1, enabled=False),  # Muted!
            ActionPoint(action=ActionType.CLICK, x=20, y=20, enabled=True),
        ]
        app = DummyApp(points, self.root)
        engine = ActionsEngine(app)

        executed = []
        engine.perform_click = lambda p, pr: executed.append((p.get("x"), p.get("y")))
        engine.interruptible_sleep = lambda d: executed.append("sleep")

        # Run click loop synchronously for 1 cycle
        engine.click_loop(random_ms=0, pos_rand=0, cycles=1)

        # The wait action (sleep) should NOT have executed because enabled=False
        self.assertEqual(executed, [(10, 10), (20, 20)])

if __name__ == "__main__":
    unittest.main()
