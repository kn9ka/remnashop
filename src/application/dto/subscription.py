from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from remnapy.enums import TrafficLimitStrategy

from src.core.enums import SubscriptionStatus
from src.core.types import RemnaUserDto
from src.core.utils.converters import bytes_to_gb

from .base import BaseDto, TrackableDto
from .plan import PlanSnapshotDto


@dataclass(kw_only=True)
class RemnaSubscriptionDto(BaseDto):
    uuid: UUID
    status: SubscriptionStatus
    expire_at: datetime
    url: str

    traffic_limit: int
    device_limit: int
    traffic_limit_strategy: Optional[TrafficLimitStrategy] = None

    tag: Optional[str] = None
    internal_squads: list[UUID] = field(default_factory=list)
    external_squad: Optional[UUID] = None

    @classmethod
    def from_remna_user(cls, remna_user: RemnaUserDto) -> "RemnaSubscriptionDto":
        return cls(
            uuid=remna_user.uuid,
            status=SubscriptionStatus(remna_user.status),
            expire_at=remna_user.expire_at,
            url=remna_user.subscription_url,  # type: ignore[arg-type]
            traffic_limit=bytes_to_gb(remna_user.traffic_limit_bytes),
            device_limit=remna_user.hwid_device_limit or 0,
            traffic_limit_strategy=TrafficLimitStrategy(remna_user.traffic_limit_strategy),
            tag=remna_user.tag,
            internal_squads=[squad.uuid for squad in remna_user.active_internal_squads],
            external_squad=remna_user.external_squad_uuid,
        )


@dataclass(kw_only=True)
class SubscriptionDto(TrackableDto):
    user_remna_id: UUID

    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    is_trial: bool = False

    traffic_limit: int
    device_limit: int
    traffic_limit_strategy: TrafficLimitStrategy

    tag: Optional[str] = None
    internal_squads: list[UUID] = field(default_factory=list)
    external_squad: Optional[UUID] = None

    expire_at: datetime
    url: str

    plan: "PlanSnapshotDto"
