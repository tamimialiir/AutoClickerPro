"""
List management module for Auto Clicker Pro.
Handles point sequence ordering, ActionCards synchronization, copy/cut/paste, and visual formatting.
"""

import copy
import tkinter as tk
from typing import Optional, Any
from theme import Theme
from logger import get_logger

logger = get_logger("ListManager")

class ListManager:
    def __init__(self, app):
        self.app = app
        self.selected_index: Optional[int] = None
        self.clipboard_point: Optional[Any] = None

    @property
    def cards_view(self):
        return getattr(self.app.gui, "action_cards_view", None)

    @property
    def points_listbox(self):
        # Backwards-compatibility property returning cards_view
        return self.cards_view

    def bind_list_shortcuts(self):
        """Bind keyboard shortcuts to the window."""
        self.app.root.bind("<Delete>", self.on_list_delete)
        self.app.root.bind("<Up>", self.on_arrow_up)
        self.app.root.bind("<Down>", self.on_arrow_down)

        for mod in ("Control", "Command"):
            self.app.root.bind(f"<{mod}-c>", lambda e: self.on_list_copy(e))
            self.app.root.bind(f"<{mod}-C>", lambda e: self.on_list_copy(e))
            self.app.root.bind(f"<{mod}-x>", lambda e: self.on_list_cut(e))
            self.app.root.bind(f"<{mod}-X>", lambda e: self.on_list_cut(e))
            self.app.root.bind(f"<{mod}-v>", lambda e: self.on_list_paste(e))
            self.app.root.bind(f"<{mod}-V>", lambda e: self.on_list_paste(e))

    def on_arrow_up(self, event=None):
        if self.app.is_focus_on_input() or self.app.is_busy():
            return
        if self.selected_index is not None and self.selected_index > 0:
            self.select_index(self.selected_index - 1)
        elif self.selected_index is None and self.app.points:
            self.select_index(len(self.app.points) - 1)
        return "break"

    def on_arrow_down(self, event=None):
        if self.app.is_focus_on_input() or self.app.is_busy():
            return
        if self.selected_index is not None and self.selected_index < len(self.app.points) - 1:
            self.select_index(self.selected_index + 1)
        elif self.selected_index is None and self.app.points:
            self.select_index(0)
        return "break"

    def on_list_delete(self, event=None):
        if self.app.is_focus_on_input() or self.app.is_busy():
            return
        if self.selected_index is not None:
            self.remove_point()
        return "break"

    def on_list_copy(self, event=None):
        if self.app.is_focus_on_input() or self.app.is_busy():
            return
        if self.selected_index is None or self.selected_index >= len(self.app.points):
            return
        self.clipboard_point = copy.deepcopy(self.app.points[self.selected_index])
        self.app.status_label.config(text="Item copied", fg=Theme.GREEN)
        return "break"

    def on_list_cut(self, event=None):
        if self.app.is_focus_on_input() or self.app.is_busy():
            return
        if self.selected_index is None or self.selected_index >= len(self.app.points):
            return
        idx = self.selected_index
        self.clipboard_point = copy.deepcopy(self.app.points[idx])
        del self.app.points[idx]
        self.refresh_points_list()
        if self.app.points:
            self.select_index(min(idx, len(self.app.points) - 1))
        else:
            self.selected_index = None
            self.app.gui.edit_btn.config(state="disabled")
        self.app.status_label.config(text="Item cut", fg=Theme.YELLOW)
        return "break"

    def on_list_paste(self, event=None):
        if self.app.is_focus_on_input() or self.app.is_busy():
            return
        if self.clipboard_point is None:
            self.app.status_label.config(text="Clipboard empty", fg=Theme.RED)
            return "break"
        new_item = copy.deepcopy(self.clipboard_point)
        if self.selected_index is not None and 0 <= self.selected_index < len(self.app.points):
            insert_at = self.selected_index + 1
        else:
            insert_at = len(self.app.points)
        self.app.points.insert(insert_at, new_item)
        self.refresh_points_list()
        self.select_index(insert_at)
        self.app.status_label.config(text="Item pasted", fg=Theme.GREEN)
        return "break"

    def highlight_current(self, index: int):
        """Highlight current active step during execution."""
        try:
            if self.cards_view:
                self.cards_view.highlight_current(index)
        except Exception as e:
            logger.debug(f"Error highlighting current step {index}: {e}")

    def clear_highlight(self):
        """Clear list selection highlighting."""
        try:
            if self.cards_view:
                self.cards_view.clear_highlight()
        except Exception as e:
            logger.debug(f"Error clearing highlight: {e}")

    def refresh_points_list(self):
        """Update items and visual formatting in the points view."""
        try:
            if self.cards_view:
                self.cards_view.render(self.app.points, selected_index=self.selected_index)
        except Exception as e:
            logger.debug(f"Error refreshing points view: {e}")

    def select_index(self, index: int):
        """Select a specific item by index."""
        if not self.app.points:
            self.selected_index = None
            if hasattr(self.app.gui, "edit_btn") and self.app.gui.edit_btn:
                self.app.gui.edit_btn.config(state="disabled")
            if self.cards_view:
                self.cards_view.selection_clear(0)
            return

        index = max(0, min(index, len(self.app.points) - 1))
        self.selected_index = index
        if self.cards_view:
            self.cards_view.select(index)
        if hasattr(self.app.gui, "edit_btn") and self.app.gui.edit_btn:
            self.app.gui.edit_btn.config(state="normal")

    def move_up(self):
        """Move selected point up in the list."""
        if self.selected_index is None or self.selected_index == 0 or self.app.is_busy():
            return
        i = self.selected_index
        self.app.points[i], self.app.points[i - 1] = self.app.points[i - 1], self.app.points[i]
        self.refresh_points_list()
        self.select_index(i - 1)

    def on_cards_reordered(self):
        """Callback when cards have been reordered via drag-and-drop."""
        if hasattr(self.app, "status_label") and self.app.status_label:
            self.app.status_label.config(text="Order changed", fg=Theme.GREEN)

    def move_down(self):
        """Move selected point down in the list."""
        if self.selected_index is None or self.selected_index >= len(self.app.points) - 1 or self.app.is_busy():
            return
        i = self.selected_index
        self.app.points[i], self.app.points[i + 1] = self.app.points[i + 1], self.app.points[i]
        self.refresh_points_list()
        self.select_index(i + 1)

    def remove_point_at(self, index: int):
        """Remove point at specific index (used by quick-action delete on card)."""
        if self.app.is_busy():
            return
        if 0 <= index < len(self.app.points):
            del self.app.points[index]
            if self.selected_index == index:
                self.selected_index = min(index, len(self.app.points) - 1) if self.app.points else None
            elif self.selected_index is not None and self.selected_index > index:
                self.selected_index -= 1
            self.refresh_points_list()
            if self.selected_index is not None:
                self.select_index(self.selected_index)
            else:
                if hasattr(self.app.gui, "edit_btn") and self.app.gui.edit_btn:
                    self.app.gui.edit_btn.config(state="disabled")
            self.app.status_label.config(text="Point removed", fg=Theme.YELLOW)

    def remove_point(self):
        """Delete currently selected point."""
        if self.app.is_busy() or self.selected_index is None:
            return
        self.remove_point_at(self.selected_index)

    def clear_points(self):
        """Remove all points from the sequence."""
        if self.app.is_busy():
            return
        self.app.points.clear()
        self.selected_index = None
        if hasattr(self.app.gui, "edit_btn") and self.app.gui.edit_btn:
            self.app.gui.edit_btn.config(state="disabled")
        self.refresh_points_list()
        self.app.status_label.config(text="All points cleared", fg=Theme.YELLOW)
