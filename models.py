"""
Data models for Auto Clicker Pro.
Defines ActionPoint with serialization, validation and backward-compatible dictionary access.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional

class ActionType:
    CLICK = "click"
    DRAG = "drag"
    SCROLL = "scroll"
    WAIT = "wait"
    KEY = "key"

@dataclass
class ActionPoint:
    action: str = ActionType.CLICK
    name: str = ""
    x: int = 0
    y: int = 0
    type: str = "Left"         # "Left", "Right", "Middle", "Double"
    hold: int = 50             # ms (click hold or drag duration)
    count: int = 1             # repeat times
    delay_after: int = 0       # ms between repeat counts
    drag_x: int = 0            # end coordinate for drag
    drag_y: int = 0
    dx: int = 0                # scroll delta x
    dy: int = 0                # scroll delta y
    delay: int = 500           # ms for wait action
    key: str = "a"             # key combo for key action
    enabled: bool = True       # whether action executes or is temporarily muted

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard profile dictionary."""
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionPoint":
        """Create ActionPoint from dictionary, ensuring fallback defaults."""
        return cls(
            action=data.get("action", ActionType.CLICK),
            name=data.get("name", ""),
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            type=data.get("type", "Left"),
            hold=int(data.get("hold", 50)),
            count=max(1, int(data.get("count", 1))),
            delay_after=max(0, int(data.get("delay_after", 0))),
            drag_x=int(data.get("drag_x", 0)),
            drag_y=int(data.get("drag_y", 0)),
            dx=int(data.get("dx", 0)),
            dy=int(data.get("dy", 0)),
            delay=max(0, int(data.get("delay", 500))),
            key=data.get("key", "a"),
            enabled=bool(data.get("enabled", True)),
        )

    # Dictionary compatibility layer to avoid breaking existing popups or list logic
    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __setitem__(self, key: str, value: Any):
        setattr(self, key, value)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def setdefault(self, key: str, default: Any = None) -> Any:
        if not hasattr(self, key) or getattr(self, key) is None:
            setattr(self, key, default)
        return getattr(self, key)
