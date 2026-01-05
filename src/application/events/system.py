from dataclasses import asdict, dataclass, field
from typing import Optional

from aiogram.types import BufferedInputFile
from aiogram.utils.formatting import Text

from src.application.dto import BuildInfoDto, MessagePayloadDto
from src.core.enums import AccessMode, MediaType, SystemNotificationType
from src.core.types import NotificationType

from .base import BaseEvent, SystemEvent


@dataclass(frozen=True, kw_only=True)
class ErrorEvent(BaseEvent, BuildInfoDto):
    notification_type: NotificationType = field(
        default=SystemNotificationType.ERROR,
        init=False,
    )

    telegram_id: Optional[int] = field(default=None)
    username: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)

    exception: BaseException

    def as_payload(
        self,
        media: BufferedInputFile,
        error: str,
        traceback: Text,
    ) -> "MessagePayloadDto":
        return MessagePayloadDto(
            i18n_key=self.event_key,
            i18n_kwargs={
                **asdict(self),
                "error": error,
                "traceback": traceback,
            },
            media=media,
            media_type=MediaType.DOCUMENT,
            disable_default_markup=False,
            delete_after=None,
        )


@dataclass(frozen=True, kw_only=True)
class RemnawaveErrorEvent(ErrorEvent):
    notification_type: NotificationType = field(
        default=SystemNotificationType.ERROR,
        init=False,
    )

    @property
    def event_key(self) -> str:
        return "event-error-remnawave"


@dataclass(frozen=True, kw_only=True)
class WebhookErrorEvent(BaseEvent):
    notification_type: NotificationType = field(
        default=SystemNotificationType.ERROR,
        init=False,
    )

    @property
    def event_key(self) -> str:
        return "event-error-webhook"

    def as_payload(
        self,
        media: BufferedInputFile,
        error: str,
        traceback: Text,
    ) -> "MessagePayloadDto":
        return MessagePayloadDto(
            i18n_key=self.event_key,
            i18n_kwargs={
                **asdict(self),
                "error": error,
                "traceback": traceback,
            },
            media=media,
            media_type=MediaType.DOCUMENT,
            delete_after=None,
        )


@dataclass(frozen=True, kw_only=True)
class BotLifecycleEvent(SystemEvent):
    notification_type: NotificationType = field(
        default=SystemNotificationType.BOT_LIFECYCLE,
        init=False,
    )


@dataclass(frozen=True, kw_only=True)
class BotStartupEvent(BotLifecycleEvent, BuildInfoDto):
    access_mode: AccessMode
    purchases_allowed: bool
    registration_allowed: bool

    @property
    def event_key(self) -> str:
        return "event-bot-startup"


@dataclass(frozen=True, kw_only=True)
class BotShutdownEvent(BotLifecycleEvent):
    @property
    def event_key(self) -> str:
        return "event-bot-shutdown"


@dataclass(frozen=True, kw_only=True)
class BotUpdateEvent(SystemEvent):
    notification_type: NotificationType = field(
        default=SystemNotificationType.BOT_UPDATE,
        init=False,
    )

    local_version: str
    remote_version: str

    def as_payload(self) -> "MessagePayloadDto":
        from src.telegram.keyboards import get_remnashop_update_keyboard  # noqa: PLC0415

        return MessagePayloadDto(
            i18n_key=self.event_key,
            i18n_kwargs={**asdict(self)},
            reply_markup=get_remnashop_update_keyboard(),
            delete_after=None,
        )


@dataclass(frozen=True, kw_only=True)
class UserRegisteredEvent(SystemEvent):
    notification_type: NotificationType = field(
        default=SystemNotificationType.USER_REGISTERED,
        init=False,
    )

    telegram_id: int
    username: Optional[str] = field(default=None)
    name: str

    referrer_telegram_id: Optional[int] = field(default=None)
    referrer_username: Optional[str] = field(default=None)
    referrer_name: Optional[str] = field(default=None)
