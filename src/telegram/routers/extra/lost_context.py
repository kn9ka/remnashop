from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager
from dishka import FromDishka
from loguru import logger

from src.application.dto import MessagePayloadDto, UserDto
from src.application.protocols import Notifier

# Registered in main router (src/bot/dispatcher.py)


async def on_lost_context(
    event: ErrorEvent,
    user: UserDto,
    dialog_manager: DialogManager,
    notifier: FromDishka[Notifier],
) -> None:
    logger.error(f"{user.log} Losted context: {event.exception}")
    await notifier.notify_user(user, payload=MessagePayloadDto(i18n_key="ntf-error-lost-context"))
