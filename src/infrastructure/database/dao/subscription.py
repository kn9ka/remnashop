from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from adaptix import Retort
from adaptix.conversion import get_converter
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import SubscriptionDto
from src.application.protocols.dao import SubscriptionDAO
from src.core.enums import SubscriptionStatus
from src.infrastructure.database.models import Subscription


class SubscriptionDAOImpl(SubscriptionDAO):
    def __init__(self, session: AsyncSession, retort: Retort, redis: Redis) -> None:
        self.session = session
        self.retort = retort
        self.redis = redis

        self._convert_to_dto = get_converter(Subscription, SubscriptionDto)
        self._convert_to_dto_list = get_converter(list[Subscription], list[SubscriptionDto])

    async def create(self, subscription: SubscriptionDto) -> SubscriptionDto:
        subscription_data = self.retort.dump(subscription)
        db_subscription = Subscription(**subscription_data)

        self.session.add(db_subscription)
        await self.session.flush()

        logger.info(
            f"New subscription '{db_subscription.id}' created "
            f"for remna user '{subscription.user_remna_id}'"
        )
        return self._convert_to_dto(db_subscription)

    async def get_by_id(self, subscription_id: int) -> Optional[SubscriptionDto]:
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        db_subscription = await self.session.scalar(stmt)

        if db_subscription:
            logger.debug(f"Subscription '{subscription_id}' found in database")
            return self._convert_to_dto(db_subscription)

        logger.debug(f"Subscription '{subscription_id}' not found")
        return None

    async def get_by_remna_id(self, user_remna_id: UUID) -> Optional[SubscriptionDto]:
        stmt = select(Subscription).where(Subscription.user_remna_id == user_remna_id)
        db_subscription = await self.session.scalar(stmt)

        if db_subscription:
            logger.debug(f"Subscription found by remna id '{user_remna_id}'")
            return self._convert_to_dto(db_subscription)

        logger.debug(f"Subscription with remna id '{user_remna_id}' not found")
        return None

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[SubscriptionDto]:
        stmt = (
            select(Subscription)
            .where(Subscription.user_telegram_id == telegram_id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        db_subscription = await self.session.scalar(stmt)

        if db_subscription:
            logger.debug(f"Last subscription for telegram user '{telegram_id}' retrieved")
            return self._convert_to_dto(db_subscription)

        return None

    async def get_all_by_user(self, telegram_id: int) -> Sequence[SubscriptionDto]:
        stmt = (
            select(Subscription)
            .where(Subscription.user_telegram_id == telegram_id)
            .order_by(Subscription.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        db_subscriptions = list(result.all())

        logger.debug(f"Retrieved '{len(db_subscriptions)}' subscriptions for user '{telegram_id}'")
        return self._convert_to_dto_list(db_subscriptions)

    async def get_current(self, telegram_id: int) -> Optional[SubscriptionDto]:
        stmt = (
            select(Subscription)
            .where(Subscription.user_telegram_id == telegram_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        db_subscription = await self.session.scalar(stmt)

        if db_subscription:
            logger.debug(f"Current active subscription found for user '{telegram_id}'")
            return self._convert_to_dto(db_subscription)

        logger.debug(f"No active current subscription for user '{telegram_id}'")
        return None

    async def update_status(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
    ) -> Optional[SubscriptionDto]:
        stmt = (
            update(Subscription)
            .where(Subscription.id == subscription_id)
            .values(status=status)
            .returning(Subscription)
        )
        db_subscription = await self.session.scalar(stmt)

        if db_subscription:
            logger.info(f"Subscription '{subscription_id}' status updated to '{status}'")
            return self._convert_to_dto(db_subscription)

        logger.warning(f"Failed to update subscription '{subscription_id}': not found")
        return None

    async def exists(self, user_remna_id: UUID) -> bool:
        stmt = select(
            select(Subscription).where(Subscription.user_remna_id == user_remna_id).exists()
        )
        is_exists = await self.session.scalar(stmt) or False

        logger.debug(f"Subscription existence check for remna id '{user_remna_id}': '{is_exists}'")
        return is_exists
