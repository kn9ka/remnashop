from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Self
from uuid import UUID

from src.core.enums import Currency, PaymentGatewayType, PurchaseType, TransactionStatus
from src.core.utils.time import datetime_now

from .base import TrackableDto
from .plan import PlanSnapshotDto


@dataclass(kw_only=True)
class PriceDetailsDto(TrackableDto):
    original_amount: Decimal
    discount_percent: int
    final_amount: Decimal

    @property
    def is_free(self) -> bool:
        return self.final_amount == 0

    @classmethod
    def test(cls) -> Self:
        return cls(
            original_amount=Decimal(2),
            discount_percent=0,
            final_amount=Decimal(2),
        )


@dataclass(kw_only=True)
class TransactionDto(TrackableDto):
    payment_id: UUID

    status: TransactionStatus
    is_test: bool = False

    purchase_type: PurchaseType
    gateway_type: PaymentGatewayType

    pricing: "PriceDetailsDto"
    currency: Currency
    plan_snapshot: "PlanSnapshotDto"

    @property
    def is_completed(self) -> bool:
        return self.status == TransactionStatus.COMPLETED

    @property
    def has_old(self) -> bool:
        if not self.created_at or self.status != TransactionStatus.PENDING:
            return False

        return datetime_now() - self.created_at > timedelta(minutes=30)
