from typing import Any, Awaitable, Callable

from aiogram.types import TelegramObject
from cachetools import TTLCache
from dishka import AsyncContainer
from loguru import logger

from src.application.dto import MessagePayloadDto, UserDto
from src.application.protocols import Notifier
from src.core.constants import CONTAINER_KEY, USER_KEY
from src.core.enums import MiddlewareEventType

from .base import EventTypedMiddleware


class ThrottlingMiddleware(EventTypedMiddleware):
    __event_types__ = [MiddlewareEventType.MESSAGE, MiddlewareEventType.CALLBACK_QUERY]

    def __init__(self, ttl: float = 0.5) -> None:
        self.cache: TTLCache[int, Any] = TTLCache(maxsize=10_000, ttl=ttl)

    async def middleware_logic(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: AsyncContainer = data[CONTAINER_KEY]
        user: UserDto = data[USER_KEY]

        notification_service: Notifier = await container.get(Notifier)

        if user.telegram_id in self.cache:
            await notification_service.notify_user(
                user=user,
                payload=MessagePayloadDto(i18n_key="ntf-throttling-many-requests"),
            )
            logger.warning(f"User '{user.telegram_id}' throttled")
            return

        self.cache[user.telegram_id] = None
        return await handler(event, data)
