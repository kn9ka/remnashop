from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import Locale, UserRole

from .base import BaseSql
from .referral import Referral
from .subscription import Subscription
from .timestamp import TimestampMixin
from .transaction import Transaction


class User(BaseSql, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True, unique=True)

    username: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    referral_code: Mapped[str] = mapped_column(String(64), index=True, unique=True)

    name: Mapped[str] = mapped_column(String(128))
    role: Mapped[UserRole] = mapped_column(index=True)
    language: Mapped[Locale]

    personal_discount: Mapped[int]
    purchase_discount: Mapped[int]
    points: Mapped[int]

    is_blocked: Mapped[bool]
    is_bot_blocked: Mapped[bool]
    is_rules_accepted: Mapped[bool]

    current_subscription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "subscriptions.id",
            ondelete="SET NULL",
        )
    )

    current_subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        foreign_keys=[current_subscription_id],
        lazy="selectin",
    )

    referral: Mapped[Optional["Referral"]] = relationship(
        "Referral",
        back_populates="referred",
        primaryjoin="User.telegram_id==Referral.referred_telegram_id",
        lazy="selectin",
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user",
        foreign_keys="[Subscription.user_telegram_id]",
    )

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
