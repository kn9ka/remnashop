from adaptix import Retort
from adaptix.conversion import coercer, get_converter
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import (
    AccessSettingsDto,
    NotificationsSettingsDto,
    ReferralSettingsDto,
    RequirementSettingsDto,
    SettingsDto,
)
from src.application.protocols.dao import SettingsDAO
from src.core.constants import TTL_6H
from src.infrastructure.database.models import Settings
from src.infrastructure.redis.cache import invalidate_cache, provide_cache
from src.infrastructure.redis.keys import SETTINGS_PREFIX


class SettingsDAOImpl(SettingsDAO):
    def __init__(self, session: AsyncSession, retort: Retort, redis: Redis) -> None:
        self.session = session
        self.retort = retort
        self.redis = redis

        self._convert_to_dto = get_converter(
            Settings,
            SettingsDto,
            recipe=[
                coercer(dict, AccessSettingsDto, retort.get_loader(AccessSettingsDto)),
                coercer(dict, RequirementSettingsDto, retort.get_loader(RequirementSettingsDto)),
                coercer(
                    dict, NotificationsSettingsDto, retort.get_loader(NotificationsSettingsDto)
                ),
                coercer(dict, ReferralSettingsDto, retort.get_loader(ReferralSettingsDto)),
            ],
        )

    async def create_default(self) -> SettingsDto:
        settings_data = self.retort.dump(SettingsDto())
        db_settings = Settings(**settings_data)
        self.session.add(db_settings)

        await self.session.flush()
        await self.session.commit()

        logger.info("Default settings record created in database")
        return self._convert_to_dto(db_settings)

    @provide_cache(prefix=SETTINGS_PREFIX, ttl=TTL_6H)
    async def get(self) -> SettingsDto:
        stmt = select(Settings).limit(1)
        db_settings = await self.session.scalar(stmt)

        if not db_settings:
            logger.debug("Settings not found in database, creating default")
            return await self.create_default()

        logger.debug("Global settings retrieved from database")
        return self._convert_to_dto(db_settings)

    @invalidate_cache(key_builder=SETTINGS_PREFIX)
    async def update(self, dto: SettingsDto) -> SettingsDto:
        if not dto.changed_data:
            logger.warning("No changes detected in settings, skipping update")
            return await self.get()

        update_data = {
            k: self.retort.dump(v) if hasattr(v, "__dataclass_fields__") else v
            for k, v in dto.changed_data.items()
        }

        stmt = (
            update(Settings).where(Settings.id == dto.id).values(**update_data).returning(Settings)
        )
        db_settings = await self.session.scalar(stmt)

        if not db_settings:
            logger.warning(f"Failed to update settings with id '{dto.id}': record not found")
            return await self.get()

        logger.info(f"Settings updated successfully with keys '{list(update_data.keys())}'")
        return self._convert_to_dto(db_settings)
