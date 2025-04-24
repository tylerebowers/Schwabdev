
from __future__ import annotations

from enum import Enum


class TimeFormat(Enum):
    ISO_8601 = "8601"
    EPOCH = "epoch"
    EPOCH_MS = "epoch_ms"
    YYYY_MM_DD = "YYYY-MM-DD"
