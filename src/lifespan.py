from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from aiogram import Bot, Dispatcher
from aiogram.types import WebhookInfo
from dishka import AsyncContainer, Scope
from fastapi import FastAPI
from loguru import logger

from src.application.events import (
    BotShutdownEvent,
    BotStartupEvent,
    RemnawaveErrorEvent,
    WebhookErrorEvent,
)
from src.application.use_cases import CommandUseCase, SettingsUseCase, WebhookUseCase
from src.core.config import AppConfig
from src.infrastructure.services import EventBusImpl
from src.web.endpoints import TelegramWebhookEndpoint


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    dispatcher: Dispatcher = app.state.dispatcher
    telegram_webhook_endpoint: TelegramWebhookEndpoint = app.state.telegram_webhook_endpoint
    container: AsyncContainer = app.state.dishka_container

    event_bus = await container.get(EventBusImpl)
    event_bus.set_container_factory(lambda: container)
    event_bus.autodiscover()

    async with container(scope=Scope.REQUEST) as startup_container:
        config: AppConfig = await startup_container.get(AppConfig)
        settings_use_case: SettingsUseCase = await startup_container.get(SettingsUseCase)
        webhook_use_case: WebhookUseCase = await startup_container.get(WebhookUseCase)
        command_use_case: CommandUseCase = await startup_container.get(CommandUseCase)

        settings = await settings_use_case.get_settings()

        allowed_updates = dispatcher.resolve_used_update_types()
        webhook_info: WebhookInfo = await webhook_use_case.setup_webhook(allowed_updates)

        if webhook_use_case.has_error(webhook_info):
            logger.critical(
                f"Webhook has a last error message: '{webhook_info.last_error_message}'"
            )
            webhook_error_event = WebhookErrorEvent()
            await event_bus.publish(webhook_error_event)

        await command_use_case.setup_commands()

    await telegram_webhook_endpoint.startup()

    bot: Bot = await container.get(Bot)
    bot_info = await bot.get_me()
    states: dict[Optional[bool], str] = {True: "Enabled", False: "Disabled", None: "Unknown"}

    logger.opt(colors=True).info(
        rf"""
    <cyan> _____                                _                 </>
    <cyan>|  __ \                              | |                </>
    <cyan>| |__) |___ _ __ ___  _ __   __ _ ___| |__   ___  _ __  </>
    <cyan>|  _  // _ \ '_ ` _ \| '_ \ / _` / __| '_ \ / _ \| '_ \ </>
    <cyan>| | \ \  __/ | | | | | | | | (_| \__ \ | | | (_) | |_) |</>
    <cyan>|_|  \_\___|_| |_| |_|_| |_|\__,_|___/_| |_|\___/| .__/ </>
    <cyan>                                                 | |    </>
    <cyan>                                                 |_|    </>

        <green>Build Time: {config.build.time}</>
        <green>Branch: {config.build.branch} ({config.build.tag})</>
        <green>Commit: {config.build.commit}</>
        <cyan>------------------------</>
        Groups Mode  - {states[bot_info.can_join_groups]}
        Privacy Mode - {states[not bot_info.can_read_all_group_messages]}
        Inline Mode  - {states[bot_info.supports_inline_queries]}
        <cyan>------------------------</>
        <yellow>Bot in access mode: '{settings.access.mode}'</>
        <yellow>Purchases allowed: '{settings.access.purchases_allowed}'</>
        <yellow>Registration allowed: '{settings.access.registration_allowed}'</>
        """  # noqa: W605
    )

    bot_startup_event = BotStartupEvent(
        **config.build.data,
        access_mode=settings.access.mode,
        purchases_allowed=settings.access.purchases_allowed,
        registration_allowed=settings.access.registration_allowed,
    )
    await event_bus.publish(bot_startup_event)

    try:
        pass
        # await remnawave_service.try_connection() #TODO: remnawave version
    except Exception as e:
        logger.exception(f"Remnawave connection failed: {e}")

        remnawave_error_event = RemnawaveErrorEvent(**config.build.data, exception=e)
        await event_bus.publish(remnawave_error_event)

    yield

    bot_shutdown_event = BotShutdownEvent()
    await event_bus.publish(bot_shutdown_event)

    await event_bus.shutdown()
    await telegram_webhook_endpoint.shutdown()
    await command_use_case.delete_commands()
    await webhook_use_case.delete_webhook()
    await container.close()
