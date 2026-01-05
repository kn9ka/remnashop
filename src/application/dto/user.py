from dataclasses import dataclass
from typing import Optional, Self

from src.core.enums import Locale, UserRole
from src.core.utils.time import datetime_now

from .base import TrackableDto


@dataclass(kw_only=True)
class UserDto(TrackableDto):
    telegram_id: int

    username: Optional[str] = None
    referral_code: str = ""

    name: str
    role: UserRole = UserRole.USER
    language: Locale = Locale.EN

    personal_discount: int = 0
    purchase_discount: int = 0
    points: int = 0

    is_blocked: bool = False
    is_bot_blocked: bool = False
    is_rules_accepted: bool = False

    @property
    def is_dev(self) -> bool:
        return self.role == UserRole.DEV

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_privileged(self) -> bool:
        return self.is_admin or self.is_dev

    @property
    def age_days(self) -> Optional[int]:
        if self.created_at is None:
            return None

        return (datetime_now() - self.created_at).days

    @property
    def log(self) -> str:
        return f"[{self.role}:{self.telegram_id} ({self.name})]"

    @classmethod
    def temp_user(cls, telegram_id: int, name: str = "TempUser") -> Self:
        return cls(telegram_id=telegram_id, name=name, role=UserRole.USER)

    @classmethod
    def temp_root(cls, telegram_id: int) -> Self:
        return cls(telegram_id=telegram_id, name="TempRoot", role=UserRole.ROOT)
