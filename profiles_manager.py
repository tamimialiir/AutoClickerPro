"""
Profile manager for Auto Clicker Pro.
Handles saving, loading, and validating profile JSON files.
"""

import json
import os
from typing import Dict, Any, List, Optional
from models import ActionPoint
from logger import get_logger

logger = get_logger("ProfilesManager")

class ProfilesManager:
    @staticmethod
    def save_profile_to_file(path: str, data: Dict[str, Any]) -> bool:
        """Write profile dictionary to a JSON file."""
        try:
            # Ensure points are serialized to dictionaries
            serialized_points = []
            for p in data.get("points", []):
                if isinstance(p, ActionPoint):
                    serialized_points.append(p.to_dict())
                elif isinstance(p, dict):
                    serialized_points.append(p)
                else:
                    serialized_points.append(dict(p))

            payload = dict(data)
            payload["points"] = serialized_points

            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully saved profile to: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile to {path}: {e}", exc_info=True)
            raise

    @staticmethod
    def load_profile_from_file(path: str) -> Dict[str, Any]:
        """Read and validate profile data from a JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_points = data.get("points", [])
            points = [ActionPoint.from_dict(p) for p in raw_points]

            result = {
                "points": points,
                "random": int(data.get("random", 0)),
                "pos_random": int(data.get("pos_random", 0)),
                "cycles": max(1, int(data.get("cycles", 1))),
                "infinite": bool(data.get("infinite", False)),
                "speed": float(data.get("speed", 1.0)),
                "start_hotkey": data.get("start_hotkey", "f1"),
                "pause_hotkey": data.get("pause_hotkey", "f2"),
                "stop_hotkey": data.get("stop_hotkey", "f3"),
                "record_start_hotkey": data.get("record_start_hotkey", "f4"),
                "record_stop_hotkey": data.get("record_stop_hotkey", "f5"),
                "start_enabled": bool(data.get("start_enabled", True)),
                "pause_enabled": bool(data.get("pause_enabled", True)),
                "stop_enabled": bool(data.get("stop_enabled", True)),
                "record_start_enabled": bool(data.get("record_start_enabled", True)),
                "record_stop_enabled": bool(data.get("record_stop_enabled", True)),
                "always_on_top": bool(data.get("always_on_top", False)),
            }
            logger.info(f"Successfully loaded profile from: {path} with {len(points)} points.")
            return result
        except Exception as e:
            logger.error(f"Failed to load profile from {path}: {e}", exc_info=True)
            raise
