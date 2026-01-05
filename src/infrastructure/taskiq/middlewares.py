from typing import Any, Optional

from dishka import AsyncContainer
from loguru import logger
from taskiq import TaskiqMessage, TaskiqResult
from taskiq.abc.middleware import TaskiqMiddleware

from src.application.events import ErrorEvent
from src.application.protocols import EventPublisher
from src.core.config import AppConfig


class ErrorMiddleware(TaskiqMiddleware):
    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
        exception: BaseException,
    ) -> None:
        logger.error(f"Task '{message.task_name}' error: {exception}")

        container: Optional[AsyncContainer] = self.broker.custom_dependency_context.get(
            AsyncContainer
        )

        if not container:
            logger.error("Dishka container not found in taskiq broker context")
            return

        config: AppConfig = await container.get(AppConfig)
        event_publisher: EventPublisher = await container.get(EventPublisher)
        error_event = ErrorEvent(**config.build.data, exception=exception)
        await event_publisher.publish(error_event)
