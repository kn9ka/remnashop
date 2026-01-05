from __future__ import annotations

from typing import Any, Optional, Sequence, cast

from adaptix import Retort
from adaptix.conversion import get_converter
from loguru import logger
from pydantic import SecretStr
from redis.asyncio import Redis
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import AnyGatewaySettingsDto, PaymentGatewayDto
from src.application.protocols.dao import PaymentGatewayDAO
from src.core.enums import Currency, PaymentGatewayType
from src.infrastructure.database.models import PaymentGateway


class PaymentGatewayDAOImpl(PaymentGatewayDAO):
    def __init__(self, session: AsyncSession, retort: Retort, redis: Redis) -> None:
        self.session = session
        self.retort = retort
        self.redis = redis

        self._convert_to_dto = get_converter(PaymentGateway, PaymentGatewayDto)
        self._convert_to_dto_list = get_converter(list[PaymentGateway], list[PaymentGatewayDto])

    async def create(self, gateway: PaymentGatewayDto) -> PaymentGatewayDto:
        gateway_data = self.retort.dump(gateway)

        if gateway_data.get("settings"):
            gateway_data["settings"] = self._process_secrets(gateway_data["settings"])

        db_gateway = PaymentGateway(**gateway_data)
        self.session.add(db_gateway)
        await self.session.flush()

        logger.info(f"Payment gateway '{gateway.type}' created in database")
        return self._convert_to_dto(db_gateway)

    async def get_by_type(self, gateway_type: PaymentGatewayType) -> Optional[PaymentGatewayDto]:
        stmt = select(PaymentGateway).where(PaymentGateway.type == gateway_type)
        db_gateway = await self.session.scalar(stmt)

        if db_gateway:
            logger.debug(f"Payment gateway '{gateway_type}' found")
            return self._convert_to_dto(db_gateway)

        logger.debug(f"Payment gateway '{gateway_type}' not found")
        return None

    async def get_active_by_currency(self, currency: Currency) -> Sequence[PaymentGatewayDto]:
        stmt = (
            select(PaymentGateway)
            .where(PaymentGateway.is_active == True)  # noqa: E712
            .where(PaymentGateway.currency == currency)
            .order_by(PaymentGateway.order_index.asc())
        )
        result = await self.session.scalars(stmt)
        db_gateways = list(result.all())

        logger.debug(f"Retrieved '{len(db_gateways)}' active gateways for currency '{currency}'")
        return self._convert_to_dto_list(db_gateways)

    async def get_all(self, only_active: bool = False) -> Sequence[PaymentGatewayDto]:
        stmt = select(PaymentGateway).order_by(PaymentGateway.order_index.asc())
        if only_active:
            stmt = stmt.where(PaymentGateway.is_active == True)  # noqa: E712

        result = await self.session.scalars(stmt)
        db_gateways = list(result.all())

        logger.debug(f"Retrieved '{len(db_gateways)}' gateways (only_active='{only_active}')")
        return self._convert_to_dto_list(db_gateways)

    async def update_settings(
        self,
        gateway_type: PaymentGatewayType,
        settings: AnyGatewaySettingsDto,
    ) -> Optional[PaymentGatewayDto]:
        settings_data = self.retort.dump(settings)
        processed_settings = self._process_secrets(settings_data)

        stmt = (
            update(PaymentGateway)
            .where(PaymentGateway.type == gateway_type)
            .values(settings=processed_settings)
            .returning(PaymentGateway)
        )
        db_gateway = await self.session.scalar(stmt)

        if db_gateway:
            logger.info(f"Settings for gateway '{gateway_type}' updated successfully")
            return self._convert_to_dto(db_gateway)

        logger.warning(f"Failed to update settings: gateway '{gateway_type}' not found")
        return None

    async def set_active_status(self, gateway_type: PaymentGatewayType, is_active: bool) -> None:
        stmt = (
            update(PaymentGateway)
            .where(PaymentGateway.type == gateway_type)
            .values(is_active=is_active)
        )
        await self.session.execute(stmt)
        logger.info(f"Gateway '{gateway_type}' active status set to '{is_active}'")

    async def count_active(self) -> int:
        stmt = (
            select(func.count()).select_from(PaymentGateway).where(PaymentGateway.is_active == True)  # noqa: E712
        )
        count = await self.session.scalar(stmt) or 0

        logger.debug(f"Active gateways count: '{count}'")
        return count

    def _process_secrets(self, data: dict[str, Any]) -> dict[str, Any]:
        processed: dict[str, Any] = {}

        for key, value in data.items():
            if isinstance(value, SecretStr):
                processed[key] = value.get_secret_value()
            elif isinstance(value, dict):
                processed[key] = self._process_secrets(cast(dict[str, Any], value))
            else:
                processed[key] = value

        return processed
