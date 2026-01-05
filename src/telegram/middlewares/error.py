from typing import Any, Awaitable, Callable, Optional, cast

from aiogram.types import ErrorEvent as AiogramErrorEvent
from aiogram.types import TelegramObject
from aiogram.types import User as AiogramUser
from aiogram_dialog.api.exceptions import (
    InvalidStackIdError,
    OutdatedIntent,
    UnknownIntent,
    UnknownState,
)
from dishka import AsyncContainer

from src.application.events import ErrorEvent
from src.application.protocols import EventPublisher
from src.core.config import AppConfig
from src.core.constants import CONFIG_KEY, CONTAINER_KEY
from src.core.enums import MiddlewareEventType

from .base import EventTypedMiddleware


class ErrorMiddleware(EventTypedMiddleware):
    __event_types__ = [MiddlewareEventType.ERROR]

    async def middleware_logic(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event = cast(AiogramErrorEvent, event)

        if type(event.exception) in [
            InvalidStackIdError,
            OutdatedIntent,
            UnknownIntent,
            UnknownState,
        ]:
            return await handler(event, data)

        aiogram_user: Optional[AiogramUser] = self._get_aiogram_user(data)
        config: AppConfig = data[CONFIG_KEY]

        container: AsyncContainer = data[CONTAINER_KEY]
        event_publisher: EventPublisher = await container.get(EventPublisher)

        # TODO: redirect to main menu (only role=user)
        # if aiogram_user:
        #     if user and not user.is_dev and not isinstance(error, MenuRenderingError):
        #         await redirect_to_main_menu_task.kiq(aiogram_user.id)

        error_event = ErrorEvent(
            **config.build.data,
            #
            telegram_id=aiogram_user.id if aiogram_user else None,
            username=aiogram_user.username if aiogram_user else None,
            name=aiogram_user.full_name if aiogram_user else None,
            #
            exception=event.exception,
        )

        await event_publisher.publish(error_event)
