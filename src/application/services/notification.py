import asyncio
import traceback
from typing import Any, Callable, Optional, Sequence

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.utils.formatting import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from src.application.dto import MessagePayloadDto, SettingsDto, UserDto
from src.application.events import ErrorEvent, SystemEvent
from src.application.protocols import Notifier, TranslatorHub
from src.application.protocols.dao import SettingsDAO, UserDAO
from src.core.config import AppConfig
from src.core.enums import Locale, UserRole
from src.core.types import AnyKeyboard
from src.infrastructure.services.event_bus import on_event
from src.telegram.states import Notification


class NotificationService(Notifier):
    def __init__(
        self,
        bot: Bot,
        config: AppConfig,
        translator_hub: TranslatorHub,
        user_dao: UserDAO,
        settings_dao: SettingsDAO,
    ) -> None:
        self.bot = bot
        self.config = config
        self.translator_hub = translator_hub
        self.user_dao = user_dao
        self.settings_dao = settings_dao

    async def notify_user(self, user: UserDto, payload: MessagePayloadDto) -> Optional[Message]:
        return await self._send_message(user, payload)

    async def notify_admins(
        self,
        payload: MessagePayloadDto,
        roles: list[UserRole] = [UserRole.ROOT, UserRole.DEV, UserRole.ADMIN],
    ) -> None:
        users = await self.user_dao.filter_by_role(roles)

        if not users:
            logger.warning(f"No users with roles '{roles}' found for notification, using fallback")
            users.append(self._get_temp_root())

        asyncio.create_task(self._broadcast(users, payload))

    @on_event(SystemEvent)
    async def on_system_event(self, event: SystemEvent) -> None:
        logger.info(f"Received '{event.event_type}' event")

        settings: SettingsDto = await self.settings_dao.get()
        if not settings.notifications.is_enabled(event.notification_type):
            logger.info(f"Notification for '{event.notification_type}' is disabled, skipping")
            return

        await self.notify_admins(event.as_payload())

    @on_event(ErrorEvent)
    async def on_error_event(self, event: ErrorEvent) -> None:
        logger.info(f"Received '{event.event_type}' event")

        error_type = type(event.exception).__name__
        error_message = Text(str(event.exception)[:512])

        traceback_str = "".join(
            traceback.format_exception(
                type(event.exception),
                event.exception,
                event.exception.__traceback__,
            )
        )

        error_file = BufferedInputFile(
            file=traceback_str.encode(),
            filename=f"error_{event.event_id}.txt",
        )

        await self.notify_admins(
            event.as_payload(error_file, error_type, error_message),
            roles=[UserRole.ROOT, UserRole.DEV],
        )

    async def delete_notification(self, chat_id: int, message_id: int) -> None:
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.debug(f"Notification '{message_id}' for chat '{chat_id}' deleted")
        except Exception as e:
            logger.error(f"Failed to delete notification '{message_id}': {e}")
            await self._clear_reply_markup(chat_id, message_id)

    async def _clear_reply_markup(self, chat_id: int, message_id: int) -> None:
        try:
            logger.debug(f"Attempting to remove keyboard from notification '{message_id}'")
            await self.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=None,
            )
            logger.debug(f"Keyboard removed from notification '{message_id}'")
        except Exception as e:
            logger.error(f"Failed to remove keyboard from '{message_id}': {e}")

    async def _broadcast(self, users: Sequence[UserDto], payload: MessagePayloadDto) -> None:
        logger.debug(f"Starting broadcast to '{len(users)}' users")
        await asyncio.gather(
            *(self._send_message(user, payload) for user in users),
            return_exceptions=True,
        )

    async def _send_message(self, user: UserDto, payload: MessagePayloadDto) -> Optional[Message]:
        reply_markup = self._prepare_reply_markup(
            payload.reply_markup,
            payload.disable_default_markup,
            payload.delete_after,
            user.language,
            user.telegram_id,
        )

        text = self._get_translated_text(
            locale=user.language,
            i18n_key=payload.i18n_key,
            i18n_kwargs=payload.i18n_kwargs,
        )

        kwargs: dict[str, Any] = {
            "disable_notification": payload.disable_notification,
            "message_effect_id": payload.message_effect,
            "reply_markup": reply_markup,
        }

        try:
            if payload.is_text:
                message = await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    disable_web_page_preview=True,
                    **kwargs,
                )
            elif payload.media:
                method = self._get_media_method(payload)

                if not method:
                    logger.warning(f"Unknown media type for payload '{payload}'")
                    return None

                message = await method(user.telegram_id, payload.media, caption=text, **kwargs)
            else:
                logger.error(f"Payload must contain text or media for user '{user.telegram_id}'")
                return None

            if message and payload.delete_after:
                asyncio.create_task(
                    self._schedule_message_deletion(
                        chat_id=user.telegram_id,
                        message_id=message.message_id,
                        delay=payload.delete_after,
                    )
                )

            return message

        except TelegramForbiddenError:
            logger.warning(f"Bot was blocked by user '{user.telegram_id}'")
            return None
        except Exception as e:
            logger.exception(f"Failed to send notification to '{user.telegram_id}': {e}")
            raise

    def _get_media_method(self, payload: MessagePayloadDto) -> Optional[Callable[..., Any]]:
        if payload.is_photo:
            return self.bot.send_photo

        if payload.is_video:
            return self.bot.send_video

        if payload.is_document:
            return self.bot.send_document

        return None

    def _get_translated_text(
        self,
        locale: Locale,
        i18n_key: str,
        i18n_kwargs: dict[str, Any] = {},
    ) -> str:
        if not i18n_key:
            return ""

        i18n = self.translator_hub.get_translator_by_locale(locale)
        return i18n.get(i18n_key, **i18n_kwargs)

    def _prepare_reply_markup(
        self,
        reply_markup: Optional[AnyKeyboard],
        disable_default_markup: bool,
        delete_after: Optional[int],
        locale: Locale,
        chat_id: int,
    ) -> Optional[AnyKeyboard]:
        if reply_markup is None:
            if not disable_default_markup and delete_after is None:
                close_button = self._get_close_notification_button(locale=locale)
                return self._get_default_keyboard(close_button)
            return None

        translated_markup = self._translate_keyboard_text(reply_markup, locale)

        if disable_default_markup or delete_after is not None:
            return translated_markup

        if isinstance(translated_markup, InlineKeyboardMarkup):
            builder = InlineKeyboardBuilder.from_markup(translated_markup)
            builder.row(self._get_close_notification_button(locale))
            return builder.as_markup()

        logger.warning(
            f"Unsupported reply_markup type '{type(reply_markup).__name__}' "
            f"for chat '{chat_id}', close button skipped"
        )
        return translated_markup

    def _get_close_notification_button(self, locale: Locale) -> InlineKeyboardButton:
        text = self._get_translated_text(locale, "btn-notification-close")
        return InlineKeyboardButton(text=text, callback_data=Notification.CLOSE.state)

    def _get_default_keyboard(self, button: InlineKeyboardButton) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder([[button]])
        return builder.as_markup()

    def _translate_keyboard_text(self, keyboard: AnyKeyboard, locale: Locale) -> AnyKeyboard:
        if isinstance(keyboard, InlineKeyboardMarkup):
            i_rows = []
            for i_row in keyboard.inline_keyboard:
                i_buttons = []
                for i_btn in i_row:
                    btn_dict = i_btn.model_dump()
                    btn_dict["text"] = self._get_translated_text(locale, i_btn.text) or i_btn.text
                    i_buttons.append(InlineKeyboardButton(**btn_dict))
                i_rows.append(i_buttons)
            return InlineKeyboardMarkup(inline_keyboard=i_rows)

        if isinstance(keyboard, ReplyKeyboardMarkup):
            r_rows = []
            for r_row in keyboard.keyboard:
                r_buttons = []
                for r_btn in r_row:
                    btn_dict = r_btn.model_dump()
                    btn_dict["text"] = self._get_translated_text(locale, r_btn.text) or r_btn.text
                    r_buttons.append(type(r_btn)(**btn_dict))
                r_rows.append(r_buttons)
            return ReplyKeyboardMarkup(keyboard=r_rows, **keyboard.model_dump(exclude={"keyboard"}))

        return keyboard

    async def _schedule_message_deletion(self, chat_id: int, message_id: int, delay: int) -> None:
        logger.debug(f"Schedule msg '{message_id}' deletion in chat '{chat_id}' after '{delay}'s")
        await asyncio.sleep(delay)
        await self.delete_notification(chat_id, message_id)

    def _get_temp_root(self) -> UserDto:
        temp_root = UserDto(
            telegram_id=self.config.bot.dev_id,
            name="TempRoot",
            role=UserRole.ROOT,
        )

        logger.debug("Fallback to temporary root user from environment for notifications")
        return temp_root
