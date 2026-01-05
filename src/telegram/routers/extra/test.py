from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.application.dto import UserDto
from src.application.protocols import TranslatorRunner
from src.application.use_cases import SettingsUseCase
from src.core.config import AppConfig
from src.infrastructure.taskiq.tasks.test import send_error_task
from src.infrastructure.taskiq.tasks.update import check_bot_update
from src.telegram.filters import RootFilter

router = Router(name=__name__)


@inject
@router.message(Command("test"), RootFilter())
async def on_test_command(
    message: Message,
    user: UserDto,
    config: AppConfig,
    settings_use_case: FromDishka[SettingsUseCase],
) -> None:
    logger.info(f"{user.log} Test command executed")
    # raise UnknownState


@inject
async def show_dev_popup(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    i18n: FromDishka[TranslatorRunner],
) -> None:
    await callback.answer(text=i18n.get("development"), show_alert=True)
