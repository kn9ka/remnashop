from typing import Optional, Protocol, Sequence

from src.application.dto import PlanDto, PlanSnapshotDto
from src.core.enums import PlanAvailability


class PlanDAO(Protocol):
    async def create(self, plan: PlanDto) -> PlanDto: ...

    async def get_by_id(self, plan_id: int) -> Optional[PlanDto]: ...

    async def get_by_name(self, name: str) -> Optional[PlanDto]: ...

    async def get_available_for_user(
        self,
        telegram_id: int,
        availability: PlanAvailability = PlanAvailability.ALL,
    ) -> Sequence[PlanDto]: ...

    async def get_all_active(self) -> Sequence[PlanDto]: ...

    async def update_status(self, plan_id: int, is_active: bool) -> Optional[PlanDto]: ...

    async def delete(self, plan_id: int) -> bool: ...
