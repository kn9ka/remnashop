from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import ReferralLevel, ReferralRewardType

from .base import BaseSql
from .timestamp import TimestampMixin


class Referral(BaseSql, TimestampMixin):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True)
    referrer_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        index=True,
    )
    referred_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        index=True,
        unique=True,
    )

    level: Mapped[ReferralLevel]

    referrer: Mapped["User"] = relationship(
        foreign_keys=[referrer_telegram_id],
        lazy="selectin",
    )
    referred: Mapped["User"] = relationship(
        back_populates="referral",
        foreign_keys=[referred_telegram_id],
        lazy="selectin",
    )
    rewards: Mapped[list["ReferralReward"]] = relationship(
        back_populates="referral",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ReferralReward(BaseSql, TimestampMixin):
    __tablename__ = "referral_rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey("referrals.id"))
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        index=True,
    )

    type: Mapped[ReferralRewardType]
    amount: Mapped[int]
    is_issued: Mapped[bool]

    referral: Mapped["Referral"] = relationship(
        back_populates="rewards",
        foreign_keys=[referral_id],
        lazy="selectin",
    )

    user: Mapped["User"] = relationship(
        foreign_keys=[user_telegram_id],
        lazy="selectin",
    )
