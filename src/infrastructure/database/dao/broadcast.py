from __future__ import annotations

from datetime import timedelta
from typing import Optional, Sequence
from uuid import UUID

from adaptix import Retort
from adaptix.conversion import get_converter
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import BroadcastDto, BroadcastMessageDto
from src.application.protocols.dao import BroadcastDAO
from src.core.enums import BroadcastMessageStatus, BroadcastStatus
from src.core.utils.time import datetime_now
from src.infrastructure.database.models import Broadcast, BroadcastMessage


class BroadcastDAOImpl(BroadcastDAO):
    def __init__(self, session: AsyncSession, retort: Retort, redis: Redis) -> None:
        self.session = session
        self.retort = retort
        self.redis = redis

        self._convert_to_dto = get_converter(Broadcast, BroadcastDto)
        self._convert_to_dto_list = get_converter(list[Broadcast], list[BroadcastDto])

    async def create(self, broadcast: BroadcastDto) -> BroadcastDto:
        broadcast_data = self.retort.dump(broadcast)
        db_broadcast = Broadcast(**broadcast_data)

        self.session.add(db_broadcast)
        await self.session.flush()

        logger.info(f"New broadcast task '{broadcast.task_id}' created in database")
        return self._convert_to_dto(db_broadcast)

    async def get_by_task_id(self, task_id: UUID) -> Optional[BroadcastDto]:
        stmt = select(Broadcast).where(Broadcast.task_id == task_id)
        db_broadcast = await self.session.scalar(stmt)

        if db_broadcast:
            logger.debug(f"Broadcast '{task_id}' found")
            return self._convert_to_dto(db_broadcast)

        logger.debug(f"Broadcast '{task_id}' not found")
        return None

    async def update_status(self, task_id: UUID, status: BroadcastStatus) -> None:
        stmt = update(Broadcast).where(Broadcast.task_id == task_id).values(status=status)
        await self.session.execute(stmt)
        logger.info(f"Broadcast '{task_id}' status updated to '{status}'")

    async def add_messages(self, task_id: UUID, messages: list[BroadcastMessageDto]) -> None:
        broadcast_id_stmt = select(Broadcast.id).where(Broadcast.task_id == task_id)
        broadcast_id = await self.session.scalar(broadcast_id_stmt)

        if not broadcast_id:
            logger.error(f"Cannot add messages: broadcast task '{task_id}' not found")
            return

        db_messages = [
            BroadcastMessage(**self.retort.dump(msg), broadcast_id=broadcast_id) for msg in messages
        ]
        self.session.add_all(db_messages)
        logger.info(f"Added '{len(messages)}' messages to broadcast task '{task_id}'")

    async def update_message_status(
        self,
        task_id: UUID,
        user_telegram_id: int,
        status: BroadcastMessageStatus,
        message_id: Optional[int] = None,
    ) -> None:
        broadcast_id_stmt = (
            select(Broadcast.id).where(Broadcast.task_id == task_id).scalar_subquery()
        )

        stmt = (
            update(BroadcastMessage)
            .where(BroadcastMessage.broadcast_id == broadcast_id_stmt)
            .where(BroadcastMessage.user_telegram_id == user_telegram_id)
            .values(status=status, message_id=message_id)
        )
        await self.session.execute(stmt)
        logger.debug(
            f"Message status for user '{user_telegram_id}' "
            f"in task '{task_id}' updated to '{status}'"
        )

    async def increment_stats(self, task_id: UUID, success: bool = True) -> None:
        field = Broadcast.success_count if success else Broadcast.failed_count
        stmt = update(Broadcast).where(Broadcast.task_id == task_id).values({field: field + 1})
        await self.session.execute(stmt)

    async def get_active(self) -> Sequence[BroadcastDto]:
        stmt = select(Broadcast).where(Broadcast.status == BroadcastStatus.PROCESSING)
        result = await self.session.scalars(stmt)
        db_broadcasts = list(result.all())

        logger.debug(f"Retrieved '{len(db_broadcasts)}' active broadcasts")
        return self._convert_to_dto_list(db_broadcasts)

    async def delete_old(self, days: int = 7) -> int:
        threshold = datetime_now() - timedelta(days=days)

        stmt = delete(Broadcast).where(Broadcast.created_at < threshold).returning(Broadcast.id)
        result = await self.session.execute(stmt)
        deleted_ids = result.scalars().all()
        count = len(deleted_ids)

        if count > 0:
            logger.info(
                f"Deleted '{count}' old broadcasts and their messages older than '{days}' days"
            )

        return count
