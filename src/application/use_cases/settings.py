from typing import Any

from loguru import logger

from src.application.dto import SettingsDto
from src.application.protocols.dao import SettingsDAO
from src.application.protocols.uow import UnitOfWork
from src.core.types import NotificationType


class SettingsUseCase:
    def __init__(
        self,
        dao: SettingsDAO,
        uow: UnitOfWork,
    ) -> None:
        self.dao = dao
        self.uow = uow

    async def get_settings(self) -> SettingsDto:
        async with self.uow:
            return await self.dao.get()

    async def toggle_notification(self, ntf_type: NotificationType) -> SettingsDto:
        async with self.uow:
            settings = await self.dao.get()
            settings.notifications.toggle(ntf_type)
            updated_settings = await self.dao.update(settings)
            await self.uow.commit()

        logger.info(f"Notification '{ntf_type}' toggled in settings")
        return updated_settings

    async def update_access_settings(self, **kwargs: Any) -> SettingsDto:
        async with self.uow:
            settings = await self.dao.get()

            for key, value in kwargs.items():
                if hasattr(settings.access, key):
                    setattr(settings.access, key, value)

            updated_settings = await self.dao.update(settings)
            await self.uow.commit()

        logger.info(f"Access settings updated with keys '{list(kwargs.keys())}'")
        return updated_settings
