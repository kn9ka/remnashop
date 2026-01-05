from aiogram import Router
from aiogram.filters import JOIN_TRANSITION, LEAVE_TRANSITION, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from dishka import FromDishka
from loguru import logger

from src.application.dto import UserDto
from src.application.use_cases import UserUseCase

# For only ChatType.PRIVATE (app/bot/filters/private.py)

router = Router(name=__name__)


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_unblocked(
    member: ChatMemberUpdated,
    user: UserDto,
    user_use_case: FromDishka[UserUseCase],
) -> None:
    logger.info(f"{user.log} Unblocked bot")
    await user_use_case.set_bot_blocked_status(user.telegram_id, False)


@router.my_chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def on_blocked(
    member: ChatMemberUpdated,
    user: UserDto,
    user_use_case: FromDishka[UserUseCase],
) -> None:
    logger.info(f"{user.log} Blocked bot")
    await user_use_case.set_bot_blocked_status(user.telegram_id, True)
