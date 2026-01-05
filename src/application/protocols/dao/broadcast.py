from typing import Optional, Protocol, Sequence
from uuid import UUID

from src.application.dto import BroadcastDto, BroadcastMessageDto
from src.core.enums import BroadcastMessageStatus, BroadcastStatus


class BroadcastDAO(Protocol):
    async def create(self, broadcast: BroadcastDto) -> BroadcastDto: ...

    async def get_by_task_id(self, task_id: UUID) -> Optional[BroadcastDto]: ...

    async def update_status(self, task_id: UUID, status: BroadcastStatus) -> None: ...

    async def add_messages(self, task_id: UUID, messages: list[BroadcastMessageDto]) -> None: ...

    async def update_message_status(
        self,
        task_id: UUID,
        user_telegram_id: int,
        status: BroadcastMessageStatus,
        message_id: Optional[int] = None,
    ) -> None: ...

    async def increment_stats(self, task_id: UUID, success: bool = True) -> None: ...

    async def get_active(self) -> Sequence[BroadcastDto]: ...

    async def delete_old(self, days: int = 7) -> int: ...
