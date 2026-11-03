from typing import Protocol

from app.infrastructure.realtime.events import RealtimeEvent


class EventPublisher(Protocol):
    async def publish(self, event: RealtimeEvent) -> None:
        ...
