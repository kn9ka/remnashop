import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Final, Optional

GB_FACTOR: Final[Decimal] = Decimal(1024**3)


def _round_decimal(value: Decimal) -> int:
    result = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return max(0, int(result))


def to_snake_case(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def event_to_key(class_name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
    formatted_key = snake.replace("_", "-")
    return f"event-{formatted_key}"


def gb_to_bytes(value: Optional[int]) -> int:
    if not value:
        return 0

    return _round_decimal(Decimal(value) * GB_FACTOR)


def bytes_to_gb(value: Optional[int]) -> int:
    if not value:
        return 0

    return _round_decimal(Decimal(value) / GB_FACTOR)
