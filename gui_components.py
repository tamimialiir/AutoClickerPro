"""
Reusable GUI components and preview overlays for Auto Clicker Pro.
"""

import tkinter as tk
from pynput import mouse
from pynput.mouse import Button
from theme import Theme
from logger import get_logger

logger = get_logger("GuiComponents")

class ToolTip:
    """Simple tooltip that appears after a short delay. All texts are English."""

    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, event=None):
        self._hide()
        self.id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(
            tw, text=self.text, justify="left",
            background=Theme.SURFACE_0, foreground=Theme.TEXT,
            relief="solid", borderwidth=1,
            font=Theme.FONT_SMALL, padx=6, pady=3
        )
        label.pack()

    def _hide(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


def clear_previews(preview_windows):
    """Safely destroy active preview overlay windows and stop listeners."""
    for w in preview_windows:
        try:
            lst = getattr(w, "_drag_listener", None)
            if lst is not None:
                try:
                    if lst.is_alive():
                        lst.stop()
                except Exception as e:
                    logger.debug(f"Error stopping drag listener: {e}")
            w.destroy()
        except Exception as e:
            logger.debug(f"Error destroying preview window: {e}")
    preview_windows.clear()


def show_point_preview(parent, preview_windows, x, y, color=Theme.RED, label=""):
    """Display an on-screen crosshair marker at the specified coordinates."""
    try:
        preview = tk.Toplevel(parent)
        preview.overrideredirect(True)
        preview.attributes("-topmost", True)
        transparent = "#010101"
        try:
            preview.attributes("-transparentcolor", transparent)
        except Exception:
            transparent = Theme.BASE
        size = 36
        preview.geometry(f"{size}x{size}+{int(x) - size // 2}+{int(y) - size // 2}")
        canvas = tk.Canvas(preview, width=size, height=size, bg=transparent, highlightthickness=0, bd=0)
        canvas.pack()
        center = size // 2
        outer_margin = 6
        inner_r = 3
        extend = 4
        line_width = 1
        canvas.create_line(outer_margin - extend, center, size - outer_margin + extend, center, fill=color, width=line_width)
        canvas.create_line(center, outer_margin - extend, center, size - outer_margin + extend, fill=color, width=line_width)

        # Small hollow circle at the center
        canvas.create_oval(center - inner_r, center - inner_r, center + inner_r, center + inner_r, fill=color, outline="")
        canvas.create_oval(center - 2, center - 2, center + 2, center + 2, fill=transparent, outline="")

        # Large hollow circle
        canvas.create_oval(center - 12, center - 12, center + 12, center + 12, outline=color, fill="", width=line_width)

        preview_windows.append(preview)
        return preview
    except Exception as e:
        logger.debug(f"Error showing point preview: {e}")
        return None


def move_preview(preview_win, x_var, y_var):
    """Reposition preview window to match coordinate variables."""
    if preview_win is None:
        return
    try:
        x, y = int(x_var.get()), int(y_var.get())
        size = 36
        preview_win.geometry(f"{size}x{size}+{x - size // 2}+{y - size // 2}")
    except Exception as e:
        logger.debug(f"Error moving preview: {e}")


def make_preview_draggable(preview_win, x_var, y_var):
    """Enable dragging the on-screen preview marker directly with the mouse."""
    if preview_win is None:
        return
    size = 36
    hit_radius = 20
    state = {"dragging": False}

    def marker_center():
        try:
            return int(x_var.get()), int(y_var.get())
        except Exception:
            return None

    def on_click(x, y, button, pressed):
        if button != Button.left:
            return True
        if pressed:
            c = marker_center()
            if c is None:
                return True
            if (x - c[0]) ** 2 + (y - c[1]) ** 2 <= hit_radius ** 2:
                state["dragging"] = True
                try:
                    preview_win.lift()
                except Exception as e:
                    logger.debug(f"Error lifting preview: {e}")
        else:
            if state["dragging"]:
                state["dragging"] = False
                try:
                    x_var.set(int(x))
                    y_var.set(int(y))
                except Exception as e:
                    logger.debug(f"Error saving drag release coords: {e}")
        return True

    def on_move(x, y):
        if not state["dragging"]:
            return True
        try:
            preview_win.geometry(f"{size}x{size}+{x - size // 2}+{y - size // 2}")
            x_var.set(int(x))
            y_var.set(int(y))
        except Exception as e:
            logger.debug(f"Error updating preview drag position: {e}")
        return True

    listener = mouse.Listener(on_click=on_click, on_move=on_move)
    listener.daemon = True
    listener.start()
    preview_win._drag_listener = listener
