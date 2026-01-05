from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional
from uuid import UUID

from src.core.enums import BroadcastAudience, BroadcastMessageStatus, BroadcastStatus
from src.core.utils.time import datetime_now

from .base import TrackableDto
from .message_payload import MessagePayloadDto


@dataclass(kw_only=True)
class BroadcastDto(TrackableDto):
    task_id: UUID

    status: BroadcastStatus
    audience: BroadcastAudience

    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0

    payload: "MessagePayloadDto"

    messages: list["BroadcastMessageDto"] = field(default_factory=list)

    @property
    def has_old(self) -> bool:
        if not self.created_at:
            return False

        is_not_processing = self.status != BroadcastStatus.PROCESSING
        is_expired = datetime_now() - self.created_at > timedelta(days=7)

        return is_not_processing and is_expired


@dataclass(kw_only=True)
class BroadcastMessageDto(TrackableDto):
    user_telegram_id: int
    message_id: Optional[int] = None

    status: BroadcastMessageStatus
