"""Human time-span parsing used by statistics commands."""

from __future__ import annotations

import re
from datetime import timedelta

DURATION_RE = re.compile(r"(\d+)\s*([mhdwy])", re.IGNORECASE)
_MULTIPLIERS = {
    "m": timedelta(minutes=1),
    "h": timedelta(hours=1),
    "d": timedelta(days=1),
    "w": timedelta(weeks=1),
    "y": timedelta(days=365),
}


def parse_duration(text: str) -> timedelta | None:
    """Parse a complete expression such as ``1h 30m``; reject partial junk."""
    normalized = re.sub(r"\s+", "", text)
    if not normalized or not re.fullmatch(r"(?:\d+[mhdwy])+", normalized, re.IGNORECASE):
        return None
    total = timedelta()
    for amount, unit in DURATION_RE.findall(normalized):
        total += int(amount) * _MULTIPLIERS[unit.lower()]
    return total
