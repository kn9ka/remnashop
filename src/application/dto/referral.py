from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.core.enums import ReferralLevel, ReferralRewardType

from .base import TrackableDto
from .user import UserDto


@dataclass(kw_only=True)
class ReferralDto(TrackableDto):
    level: ReferralLevel

    referrer: "UserDto"
    referred: "UserDto"


@dataclass(kw_only=True)
class ReferralRewardDto(TrackableDto):
    type: ReferralRewardType
    amount: int
    is_issued: bool = False

    @property
    def rewarded_at(self) -> Optional[datetime]:
        return self.created_at
