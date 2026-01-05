from dataclasses import dataclass, fields
from typing import Any, Literal, Optional, Union
from uuid import UUID

from pydantic import SecretStr

from src.core.enums import Currency, PaymentGatewayType, YookassaVatCode

from .base import BaseDto, TrackableDto


@dataclass(kw_only=True)
class PaymentResult(BaseDto):
    id: UUID
    url: Optional[str] = None


@dataclass(kw_only=True)
class PaymentGatewayDto(TrackableDto):
    order_index: int
    type: PaymentGatewayType
    currency: Currency

    is_active: bool
    settings: Optional["AnyGatewaySettingsDto"] = None

    @property
    def requires_webhook(self) -> bool:
        return self.type not in {
            PaymentGatewayType.CRYPTOMUS,
            PaymentGatewayType.HELEKET,
        }


@dataclass(kw_only=True)
class GatewaySettingsDto(TrackableDto):
    @property
    def is_configured(self) -> bool:
        for f in fields(self):
            if f.name in {"created_at", "updated_at", "type"}:
                continue
            if getattr(self, f.name) is None:
                return False
        return True

    @property
    def settings_list(self) -> list[dict[str, Any]]:
        return [
            {"field": f.name, "value": getattr(self, f.name)}
            for f in fields(self)
            if f.name not in {"type", "created_at", "updated_at"}
        ]


@dataclass(kw_only=True)
class YookassaGatewaySettingsDto(GatewaySettingsDto):
    type: Literal[PaymentGatewayType.YOOKASSA] = PaymentGatewayType.YOOKASSA
    shop_id: Optional[str] = None
    api_key: Optional[SecretStr] = None
    customer: Optional[str] = None
    vat_code: Optional[YookassaVatCode] = None


@dataclass(kw_only=True)
class YoomoneyGatewaySettingsDto(GatewaySettingsDto):
    type: Literal[PaymentGatewayType.YOOMONEY] = PaymentGatewayType.YOOMONEY
    wallet_id: Optional[str] = None
    secret_key: Optional[SecretStr] = None


@dataclass(kw_only=True)
class CryptomusGatewaySettingsDto(GatewaySettingsDto):
    type: Literal[PaymentGatewayType.CRYPTOMUS] = PaymentGatewayType.CRYPTOMUS
    merchant_id: Optional[str] = None
    api_key: Optional[SecretStr] = None


@dataclass(kw_only=True)
class HeleketGatewaySettingsDto(GatewaySettingsDto):
    type: Literal[PaymentGatewayType.HELEKET] = PaymentGatewayType.HELEKET
    merchant_id: Optional[str] = None
    api_key: Optional[SecretStr] = None


@dataclass(kw_only=True)
class CryptopayGatewaySettingsDto(GatewaySettingsDto):
    type: Literal[PaymentGatewayType.CRYPTOPAY] = PaymentGatewayType.CRYPTOPAY
    shop_id: Optional[str] = None
    api_key: Optional[SecretStr] = None
    secret_key: Optional[SecretStr] = None


@dataclass(kw_only=True)
class RobokassaGatewaySettingsDto(GatewaySettingsDto):
    type: Literal[PaymentGatewayType.ROBOKASSA] = PaymentGatewayType.ROBOKASSA
    shop_id: Optional[str] = None
    api_key: Optional[SecretStr] = None
    secret_key: Optional[SecretStr] = None


AnyGatewaySettingsDto = Union[
    YookassaGatewaySettingsDto,
    YoomoneyGatewaySettingsDto,
    CryptomusGatewaySettingsDto,
    HeleketGatewaySettingsDto,
    CryptopayGatewaySettingsDto,
    RobokassaGatewaySettingsDto,
]
