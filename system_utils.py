"""
System and OS interaction utilities for Auto Clicker Pro.
"""

import platform
import ctypes
import tkinter as tk
from logger import get_logger

logger = get_logger("SystemUtils")

def force_english_keyboard():
    """Ensure keyboard layout is set to English on Windows to avoid key mapping issues."""
    if platform.system() == "Windows":
        try:
            # 00000409 = US English
            ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 1)
        except Exception as e:
            logger.debug(f"Failed to switch keyboard layout: {e}")

def is_focus_on_input(root: tk.Tk) -> bool:
    """Check whether the currently focused widget is a text input control."""
    try:
        focused = root.focus_get()
        if focused is None:
            return False
        return focused.winfo_class() in ("TEntry", "TSpinbox", "Entry", "Spinbox")
    except Exception as e:
        logger.debug(f"Error checking focus widget: {e}")
        return False

def center_window(window: tk.Tk, width: int = 540, offset_y: int = -30):
    """Center a Tkinter window on the primary screen."""
    try:
        window.update_idletasks()
        req_h = window.winfo_reqheight()
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, ((screen_h - req_h) // 2) + offset_y)
        window.geometry(f"{width}x{req_h}+{x}+{y}")
    except Exception as e:
        logger.debug(f"Error centering window: {e}")
