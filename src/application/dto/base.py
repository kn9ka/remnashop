from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(kw_only=True)
class BaseDto:
    pass


@dataclass(kw_only=True)
class TrackableDto(BaseDto):
    id: Optional[int] = field(default=None)
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)

    _changed_data: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._initialized = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_initialized", False) and name not in ("_changed_data", "_initialized"):
            if getattr(self, name, None) != value:
                self._changed_data[name] = value

        super().__setattr__(name, value)

    @property
    def changed_data(self) -> dict[str, Any]:
        return self._changed_data
