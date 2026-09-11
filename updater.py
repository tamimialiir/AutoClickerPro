"""
GitHub update checking module for Auto Clicker Pro.
"""

import re
import json
import urllib.request
import threading
import webbrowser
from typing import Callable, Optional
from logger import get_logger

logger = get_logger("Updater")

def parse_version(tag: str) -> tuple:
    """Parse version string into integer tuple for comparison (e.g. 'v5.2' -> (5, 2))."""
    nums = re.findall(r"\d+", str(tag))
    return tuple(int(n) for n in nums) if nums else (0,)

def check_for_updates_async(
    current_version: str,
    repo: str,
    on_update_found: Callable[[str, str], None],
    on_up_to_date: Callable[[], None],
    on_error: Callable[[str], None]
):
    """
    Check GitHub Releases asynchronously for a newer version.
    Callbacks are executed, but caller should marshal them to GUI thread (e.g. via root.after).
    """
    def worker():
        try:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            logger.info(f"Checking for updates from {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "AutoClickerPro"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            latest_tag = data.get("tag_name") or data.get("name") or ""
            releases_url = data.get("html_url") or f"https://github.com/{repo}/releases"
            current = parse_version(current_version)
            latest = parse_version(latest_tag)

            logger.info(f"Current version: {current}, Latest version: {latest} ({latest_tag})")
            if latest > current:
                on_update_found(latest_tag, releases_url)
            else:
                on_up_to_date()
        except Exception as e:
            logger.warning(f"Update check failed: {e}")
            on_error(str(e))

    threading.Thread(target=worker, daemon=True).start()
