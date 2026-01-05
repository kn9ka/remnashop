from typing import Optional, Protocol

from aiogram.types import Message

from src.application.dto import MessagePayloadDto, UserDto
from src.core.enums import UserRole


class Notifier(Protocol):
    async def notify_user(
        self,
        user: UserDto,
        payload: MessagePayloadDto,
    ) -> Optional[Message]: ...

    async def notify_admins(
        self,
        payload: MessagePayloadDto,
        roles: list[UserRole] = [UserRole.ROOT, UserRole.DEV, UserRole.ADMIN],
    ) -> None: ...

    async def delete_notification(self, chat_id: int, message_id: int) -> None: ...
