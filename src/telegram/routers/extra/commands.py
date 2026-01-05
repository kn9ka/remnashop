from aiogram import Router
from aiogram.filters import Command as FilterCommand
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.application.dto import MessagePayloadDto, UserDto
from src.application.protocols import Notifier, TranslatorRunner
from src.core.config import AppConfig
from src.core.enums import Command
from src.telegram.keyboards import get_contact_support_keyboard

router = Router(name=__name__)


@inject
@router.message(FilterCommand(Command.PAYSUPPORT.value.command))
async def on_paysupport_command(
    message: Message,
    user: UserDto,
    config: AppConfig,
    i18n: FromDishka[TranslatorRunner],
    notifier: FromDishka[Notifier],
) -> None:
    logger.info(f"{user.log} Called '/paysupport' command")

    text = i18n.get("contact-support-paysupport")
    support_username = config.bot.support_username.get_secret_value()

    await notifier.notify_user(
        user=user,
        payload=MessagePayloadDto(
            i18n_key="ntf-command-paysupport",
            reply_markup=get_contact_support_keyboard(support_username, text),
            delete_after=False,
        ),
    )


@inject
@router.message(FilterCommand(Command.HELP.value.command))
async def on_help_command(
    message: Message,
    user: UserDto,
    config: AppConfig,
    i18n: FromDishka[TranslatorRunner],
    notifier: FromDishka[Notifier],
) -> None:
    logger.info(f"{user.log} Called '/help' command")

    text = i18n.get("contact-support-help")
    support_username = config.bot.support_username.get_secret_value()

    await notifier.notify_user(
        user=user,
        payload=MessagePayloadDto(
            i18n_key="ntf-command-help",
            reply_markup=get_contact_support_keyboard(support_username, text),
            delete_after=False,
        ),
    )
