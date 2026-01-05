from __future__ import annotations

from typing import Optional, Sequence

from adaptix import Retort
from adaptix.conversion import get_converter
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.dto import PlanDto
from src.application.protocols.dao import PlanDAO
from src.core.enums import PlanAvailability
from src.infrastructure.database.models import Plan, PlanDuration


class PlanDAOImpl(PlanDAO):
    def __init__(self, session: AsyncSession, retort: Retort, redis: Redis) -> None:
        self.session = session
        self.retort = retort
        self.redis = redis

        self._convert_to_dto = get_converter(Plan, PlanDto)
        self._convert_to_dto_list = get_converter(list[Plan], list[PlanDto])

    async def create(self, plan: PlanDto) -> PlanDto:
        plan_data = self.retort.dump(plan)
        db_plan = Plan(**plan_data)

        self.session.add(db_plan)
        await self.session.flush()

        logger.info(f"New plan '{plan.name}' created with '{len(plan.durations)}' durations")
        return self._convert_to_dto(db_plan)

    async def get_by_id(self, plan_id: int) -> Optional[PlanDto]:
        stmt = (
            select(Plan)
            .where(Plan.id == plan_id)
            .options(selectinload(Plan.durations).selectinload(PlanDuration.prices))
        )
        db_plan = await self.session.scalar(stmt)

        if db_plan:
            logger.debug(f"Plan '{plan_id}' found in database")
            return self._convert_to_dto(db_plan)

        logger.debug(f"Plan '{plan_id}' not found")
        return None

    async def get_by_name(self, name: str) -> Optional[PlanDto]:
        stmt = (
            select(Plan)
            .where(Plan.name == name)
            .options(selectinload(Plan.durations).selectinload(PlanDuration.prices))
        )
        db_plan = await self.session.scalar(stmt)

        if db_plan:
            logger.debug(f"Plan with name '{name}' found")
            return self._convert_to_dto(db_plan)

        return None

    async def get_available_for_user(
        self,
        telegram_id: int,
        availability: PlanAvailability = PlanAvailability.ALL,
    ) -> Sequence[PlanDto]:
        stmt = (
            select(Plan)
            .where(Plan.is_active == True)  # noqa: E712
            .where(Plan.availability == availability)
            .where(
                or_(
                    Plan.allowed_user_ids.any(telegram_id == Plan.allowed_user_ids.column_valued()),
                    func.cardinality(Plan.allowed_user_ids) == 0,
                )
            )
            .options(selectinload(Plan.durations).selectinload(PlanDuration.prices))
            .order_by(Plan.order_index.asc())
        )
        result = await self.session.scalars(stmt)
        db_plans = list(result.all())

        logger.debug(f"Retrieved '{len(db_plans)}' plans available for user '{telegram_id}'")
        return self._convert_to_dto_list(db_plans)

    async def get_all_active(self) -> Sequence[PlanDto]:
        stmt = (
            select(Plan)
            .where(Plan.is_active == True)  # noqa: E712
            .options(selectinload(Plan.durations).selectinload(PlanDuration.prices))
            .order_by(Plan.order_index.asc())
        )
        result = await self.session.scalars(stmt)
        db_plans = list(result.all())

        logger.debug(f"Retrieved '{len(db_plans)}' active plans")
        return self._convert_to_dto_list(db_plans)

    async def update_status(self, plan_id: int, is_active: bool) -> Optional[PlanDto]:
        stmt = update(Plan).where(Plan.id == plan_id).values(is_active=is_active).returning(Plan)
        db_plan = await self.session.scalar(stmt)

        if db_plan:
            logger.info(f"Plan '{plan_id}' active status set to '{is_active}'")
            return self._convert_to_dto(db_plan)

        return None

    async def delete(self, plan_id: int) -> bool:
        stmt = delete(Plan).where(Plan.id == plan_id).returning(Plan.id)
        result = await self.session.execute(stmt)
        deleted_id = result.scalar_one_or_none()

        if deleted_id:
            logger.info(f"Plan '{plan_id}' and its durations/prices deleted")
            return True

        return False
