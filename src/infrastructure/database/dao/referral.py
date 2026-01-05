from __future__ import annotations

from typing import Optional, Sequence

from adaptix import Retort
from adaptix.conversion import get_converter
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.dto import ReferralDto, ReferralRewardDto
from src.application.protocols.dao import ReferralDAO
from src.core.enums import ReferralRewardType
from src.infrastructure.database.models import Referral, ReferralReward


class ReferralDAOImpl(ReferralDAO):
    def __init__(self, session: AsyncSession, retort: Retort, redis: Redis) -> None:
        self.session = session
        self.retort = retort
        self.redis = redis

        self._convert_to_referral_dto = get_converter(Referral, ReferralDto)
        self._convert_to_referral_list = get_converter(list[Referral], list[ReferralDto])
        self._convert_to_reward_dto = get_converter(ReferralReward, ReferralRewardDto)
        self._convert_to_reward_list = get_converter(list[ReferralReward], list[ReferralRewardDto])

    async def create_referral(self, referral: ReferralDto) -> ReferralDto:
        referral_data = self.retort.dump(referral)
        db_referral = Referral(**referral_data)

        self.session.add(db_referral)
        await self.session.flush()

        logger.info(
            f"Referral link created: '{referral.referrer.telegram_id}' "
            f"invited '{referral.referred.telegram_id}'"
        )
        return self._convert_to_referral_dto(db_referral)

    async def get_by_referred_id(self, referred_id: int) -> Optional[ReferralDto]:
        stmt = (
            select(Referral)
            .where(Referral.referred_telegram_id == referred_id)
            .options(selectinload(Referral.referrer), selectinload(Referral.referred))
        )
        db_referral = await self.session.scalar(stmt)

        if db_referral:
            logger.debug(f"Referrer for user '{referred_id}' found in database")
            return self._convert_to_referral_dto(db_referral)

        logger.debug(f"No referrer found for user '{referred_id}'")
        return None

    async def get_referrals_count(self, referrer_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Referral)
            .where(Referral.referrer_telegram_id == referrer_id)
        )
        count = await self.session.scalar(stmt) or 0

        logger.debug(f"User '{referrer_id}' has '{count}' referrals")
        return count

    async def get_referrals_list(
        self,
        referrer_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ReferralDto]:
        stmt = (
            select(Referral)
            .where(Referral.referrer_telegram_id == referrer_id)
            .options(selectinload(Referral.referred))
            .limit(limit)
            .offset(offset)
            .order_by(Referral.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        db_referrals = list(result.all())

        logger.debug(f"Retrieved '{len(db_referrals)}' referrals for user '{referrer_id}'")
        return self._convert_to_referral_list(db_referrals)

    async def create_reward(
        self,
        reward: ReferralRewardDto,
        referral_id: int,
    ) -> ReferralRewardDto:
        reward_data = self.retort.dump(reward)
        db_reward = ReferralReward(**reward_data, referral_id=referral_id)

        self.session.add(db_reward)
        await self.session.flush()

        logger.info(f"Reward of amount '{reward.amount}' created for referral link '{referral_id}'")
        return self._convert_to_reward_dto(db_reward)

    async def get_pending_rewards(self) -> Sequence[ReferralRewardDto]:
        stmt = select(ReferralReward).where(ReferralReward.is_issued == False)  # noqa: E712
        result = await self.session.scalars(stmt)
        db_rewards = list(result.all())

        logger.debug(f"Found '{len(db_rewards)}' pending rewards")
        return self._convert_to_reward_list(db_rewards)

    async def mark_reward_as_issued(self, reward_id: int) -> None:
        stmt = update(ReferralReward).where(ReferralReward.id == reward_id).values(is_issued=True)
        await self.session.execute(stmt)
        logger.info(f"Reward '{reward_id}' marked as issued")

    async def get_total_rewards_amount(
        self,
        user_id: int,
        reward_type: ReferralRewardType,
    ) -> int:
        stmt = (
            select(func.sum(ReferralReward.amount))
            .where(ReferralReward.user_telegram_id == user_id)
            .where(ReferralReward.type == reward_type)
            .where(ReferralReward.is_issued == True)  # noqa: E712
        )
        total = await self.session.scalar(stmt) or 0

        logger.debug(f"Total rewards for user '{user_id}' with type '{reward_type}' is '{total}'")
        return int(total)
