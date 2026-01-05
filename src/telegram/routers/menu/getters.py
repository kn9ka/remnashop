from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.application.dto import UserDto
from src.application.protocols import TranslatorRunner
from src.core.config import AppConfig
from src.core.exceptions import MenuRenderingError
from src.telegram.utils import username_to_url


@inject
async def menu_getter(
    dialog_manager: DialogManager,
    config: AppConfig,
    user: UserDto,
    i18n: FromDishka[TranslatorRunner],
    # plan_service: FromDishka[PlanService],
    # subscription_service: FromDishka[SubscriptionService],
    # settings_service: FromDishka[SettingsService],
    # referral_service: FromDishka[ReferralService],
    **kwargs: Any,
) -> dict[str, Any]:
    return {}
    # try:
    #     plan = await plan_service.get_trial_plan()
    #     has_used_trial = await subscription_service.has_used_trial(user.telegram_id)
    #     support_username = config.bot.support_username.get_secret_value()
    #     ref_link = await referral_service.get_ref_link(user.referral_code)
    #     support_link = username_to_url(support_username, i18n.get("contact-support-help"))

    #     base_data = {
    #         "telegram_id": str(user.telegram_id),
    #         "name": user.name,
    #         "personal_discount": user.personal_discount,
    #         "support": support_link,
    #         "invite": i18n.get("referral-invite-message", url=ref_link),
    #         "has_subscription": user.has_subscription,
    #         "is_app": config.bot.is_mini_app,
    #         "is_referral_enable": await settings_service.is_referral_enable(),
    #     }

    #     subscription = user.current_subscription

    #     if not subscription:
    #         base_data.update(
    #             {
    #                 "status": None,
    #                 "is_trial": False,
    #                 "trial_available": not has_used_trial and plan,
    #                 "has_device_limit": False,
    #                 "connectable": False,
    #             }
    #         )
    #         return base_data

    #     base_data.update(
    #         {
    #             "status": subscription.get_status,
    #             "type": subscription.get_subscription_type,
    #             "traffic_limit": i18n_format_traffic_limit(subscription.traffic_limit),
    #             "device_limit": i18n_format_device_limit(subscription.device_limit),
    #             "expire_time": i18n_format_expire_time(subscription.expire_at),
    #             "is_trial": subscription.is_trial,
    #             "traffic_strategy": subscription.traffic_limit_strategy,
    #             "reset_time": subscription.get_expire_time,
    #             "has_device_limit": subscription.has_devices_limit
    #             if subscription.is_active
    #             else False,
    #             "connectable": subscription.is_active,
    #             "url": config.bot.mini_app_url or subscription.url,
    #         }
    #     )

    #     return base_data
    # except Exception as exception:
    #     raise MenuRenderingError(str(exception)) from exception
