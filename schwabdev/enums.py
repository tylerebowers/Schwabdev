
from __future__ import annotations

from enum import Enum, IntEnum


class TimeFormat(Enum):
    ISO_8601 = "8601"
    EPOCH = "epoch"
    EPOCH_MS = "epoch_ms"
    YYYY_MM_DD = "YYYY-MM-DD"

class DaysOfWeek(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_integer_list(cls, integers: list[int]) -> set[DaysOfWeek]:
        result = set()
        for int_value in integers:
            try:
                result.add(cls(int_value))
            except ValueError:
                raise ValueError(f"{int_value} is not a valid week day value. Valid values are 0 (Monday) to 6 (Sunday).")
        return result

    @classmethod
    def all_weekdays(cls) -> set[DaysOfWeek]:
        return {cls.MONDAY, cls.TUESDAY, cls.WEDNESDAY, cls.THURSDAY, cls.FRIDAY}

    @classmethod
    def all_days(cls) -> set[DaysOfWeek]:
        return {cls.MONDAY, cls.TUESDAY, cls.WEDNESDAY, cls.THURSDAY, cls.FRIDAY, cls.SATURDAY, cls.SUNDAY}
