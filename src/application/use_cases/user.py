from typing import Optional

from aiogram.types import User as AiogramUser
from loguru import logger

from src.application.dto import UserDto
from src.application.events import UserRegisteredEvent
from src.application.protocols import Cryptographer, EventPublisher
from src.application.protocols.dao import UserDAO
from src.application.protocols.uow import UnitOfWork
from src.core.config import AppConfig
from src.core.enums import Locale, UserRole


class UserUseCase:
    def __init__(
        self,
        dao: UserDAO,
        uow: UnitOfWork,
        config: AppConfig,
        cryptographer: Cryptographer,
        event_publisher: EventPublisher,
    ) -> None:
        self.dao = dao
        self.uow = uow
        self.config = config
        self.cryptographer = cryptographer
        self.event_publisher = event_publisher

    async def get_or_create_user(self, aiogram_user: AiogramUser) -> UserDto:
        async with self.uow:
            user = await self.dao.get_by_telegram_id(aiogram_user.id)
            if user is not None:
                return user

            user = UserDto(
                telegram_id=aiogram_user.id,
                username=aiogram_user.username,
                referral_code=self.cryptographer.generate_short_code(aiogram_user.id),
                name=aiogram_user.full_name,
                role=UserRole.DEV if aiogram_user.id == self.config.bot.dev_id else UserRole.USER,
                language=(
                    Locale(aiogram_user.language_code)
                    if aiogram_user.language_code in self.config.locales
                    else self.config.default_locale
                ),
            )

            user = await self.dao.create(user)
            await self.uow.commit()

        user_registered_event = UserRegisteredEvent(
            telegram_id=user.telegram_id,
            username=user.username,
            name=user.name,
        )

        await self.event_publisher.publish(user_registered_event)
        logger.info(f"User '{user.telegram_id}' created")
        return user

    async def get_user(self, telegram_id: int) -> Optional[UserDto]:
        async with self.uow:
            return await self.dao.get_by_telegram_id(telegram_id)

    async def set_bot_blocked_status(self, telegram_id: int, is_bot_blocked: bool) -> None:
        async with self.uow:
            await self.dao.set_bot_blocked_status(telegram_id, is_bot_blocked)
            await self.uow.commit()

        logger.info(f"Bot blocked status for user '{telegram_id}' set to '{is_bot_blocked}'")
