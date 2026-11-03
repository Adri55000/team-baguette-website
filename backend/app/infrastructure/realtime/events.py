from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RealtimeEvent:
    channel: str
    event_type: str
    payload: dict[str, Any]
