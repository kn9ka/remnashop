from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram_dialog.api.exceptions import (
    InvalidStackIdError,
    OutdatedIntent,
    UnknownIntent,
    UnknownState,
)

from . import extra, menu


def setup_routers(router: Router) -> None:
    # WARNING: The order of router registration matters!
    routers = [
        extra.payment.router,
        extra.notification.router,
        extra.test.router,
        extra.commands.router,
        extra.member.router,
        extra.goto.router,
        #
        menu.handlers.router,
        menu.dialog.router,
    ]

    router.include_routers(*routers)


def setup_error_handler(router: Router) -> None:
    router.errors.register(
        extra.lost_context.on_lost_context,
        ExceptionTypeFilter(UnknownIntent, UnknownState, OutdatedIntent, InvalidStackIdError),
    )
