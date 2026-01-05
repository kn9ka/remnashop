from aiogram_dialog import Dialog, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Row,
    Start,
    SwitchInlineQueryChosenChatButton,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.text import Format
from magic_filter import F

from src.core.constants import MIDDLEWARE_DATA_KEY, PURCHASE_PREFIX, USER_KEY
from src.core.enums import BannerName, MessageEffectId
from src.telegram.states import Dashboard, MainMenu
from src.telegram.widgets import Banner, Effect, I18nFormat, IgnoreUpdate
from src.telegram.window import Window

from .getters import menu_getter

menu = Window(
    Banner(BannerName.MENU),
    I18nFormat("msg-main-menu"),
    # Row(
    #     *connect_buttons,
    #     Button(
    #         text=I18nFormat("btn-menu-connect-not-available"),
    #         id="not_available",
    #         on_click=show_reason,
    #         when=~F["connectable"],
    #     ),
    #     when=F["has_subscription"],
    # ),
    # Row(
    #     Button(
    #         text=I18nFormat("btn-menu-trial"),
    #         id="trial",
    #         on_click=on_get_trial,
    #         when=F["trial_available"],
    #     ),
    # ),
    # Row(
    #     SwitchTo(
    #         text=I18nFormat("btn-menu-devices"),
    #         id="devices",
    #         state=MainMenu.DEVICES,
    #         when=F["has_device_limit"],
    #     ),
    #     Start(
    #         text=I18nFormat("btn-menu-subscription"),
    #         id=f"{PURCHASE_PREFIX}subscription",
    #         state=Subscription.MAIN,
    #     ),
    # ),
    # Row(
    #     Button(
    #         text=I18nFormat("btn-menu-invite"),
    #         id="invite",
    #         on_click=on_invite,
    #         when=F["is_referral_enable"],
    #     ),
    #     SwitchInlineQueryChosenChatButton(
    #         text=I18nFormat("btn-menu-invite"),
    #         query=Format("{invite}"),
    #         allow_user_chats=True,
    #         allow_group_chats=True,
    #         allow_channel_chats=True,
    #         id="send",
    #         when=~F["is_referral_enable"],
    #     ),
    #     Url(
    #         text=I18nFormat("btn-menu-support"),
    #         id="support",
    #         url=Format("{support}"),
    #     ),
    # ),
    # Row(
    #     Start(
    #         text=I18nFormat("btn-menu-dashboard"),
    #         id="dashboard",
    #         state=Dashboard.MAIN,
    #         mode=StartMode.RESET_STACK,
    #         when=F[MIDDLEWARE_DATA_KEY][USER_KEY].is_privileged,
    #     ),
    # ),
    # MessageInput(func=on_user_search),
    IgnoreUpdate(),
    state=MainMenu.MAIN,
    getter=menu_getter,
)

router = Dialog(menu)
