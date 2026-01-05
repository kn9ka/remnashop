from typing import Optional, Protocol, Sequence
from uuid import UUID

from src.application.dto import SubscriptionDto
from src.core.enums import SubscriptionStatus


class SubscriptionDAO(Protocol):
    async def create(self, subscription: SubscriptionDto) -> SubscriptionDto: ...

    async def get_by_id(self, subscription_id: int) -> Optional[SubscriptionDto]: ...

    async def get_by_remna_id(self, user_remna_id: UUID) -> Optional[SubscriptionDto]: ...

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[SubscriptionDto]: ...

    async def get_all_by_user(self, telegram_id: int) -> Sequence[SubscriptionDto]: ...

    async def get_current(self, telegram_id: int) -> Optional[SubscriptionDto]: ...

    async def update_status(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
    ) -> Optional[SubscriptionDto]: ...

    async def exists(self, user_remna_id: UUID) -> bool: ...
