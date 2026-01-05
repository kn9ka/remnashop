from typing import Callable, Protocol

from dishka import AsyncContainer

from src.application.events import BaseEvent


class EventPublisher(Protocol):
    async def publish(self, event: BaseEvent) -> None: ...


class EventSubscriber(Protocol):
    def autodiscover(self) -> None: ...

    async def shutdown(self) -> None: ...

    def set_container_factory(self, factory: Callable[[], AsyncContainer]) -> None: ...
