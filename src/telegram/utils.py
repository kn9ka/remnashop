from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import quote

from aiogram_dialog import DialogManager

from src.core.constants import T_ME
from src.core.utils.time import datetime_now


def is_double_click(dialog_manager: DialogManager, key: str, cooldown: int = 10) -> bool:
    now = datetime_now()
    last_click_str: Optional[str] = dialog_manager.dialog_data.get(key)
    if last_click_str:
        last_click = datetime.fromisoformat(last_click_str.replace("Z", "+00:00"))
        if now - last_click < timedelta(seconds=cooldown):
            return True

    dialog_manager.dialog_data[key] = now.isoformat()
    return False


def username_to_url(username: str, text: Optional[str]) -> str:
    clean_username = username.lstrip("@")
    encoded_text = quote(text or "")
    return f"{T_ME}{clean_username}?text={encoded_text}"
