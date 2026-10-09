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
MAX_DURATION = timedelta(days=365 * 100)


def parse_duration(text: str) -> timedelta | None:
    """Parse a complete expression such as ``1h 30m``; reject partial junk.

    Durations are bounded so hostile input cannot trigger huge integer work or
    overflow when the result is subtracted from a datetime.
    """
    normalized = re.sub(r"\s+", "", text)
    if not normalized or not re.fullmatch(r"(?:\d+[mhdwy])+", normalized, re.IGNORECASE):
        return None
    total = timedelta()
    for amount, unit in DURATION_RE.findall(normalized):
        if len(amount) > 6:
            return None
        try:
            total += int(amount) * _MULTIPLIERS[unit.lower()]
        except OverflowError:
            return None
        if total > MAX_DURATION:
            return None
    return total


def format_duration(value: timedelta) -> str:
    """Format a non-negative duration as a short canonical label."""
    total_minutes = int(value.total_seconds() // 60)
    if total_minutes < 0:
        raise ValueError("duration cannot be negative")
    units = (
        (365 * 24 * 60, "yr"),
        (7 * 24 * 60, "wk"),
        (24 * 60, "day"),
        (60, "hr"),
        (1, "min"),
    )
    parts: list[str] = []
    remaining = total_minutes
    for minutes, label in units:
        amount, remaining = divmod(remaining, minutes)
        if amount:
            parts.append(f"{amount}{label}")
    return " ".join(parts) or "0min"
