"""Pure statistics presentation types and formatting helpers."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MediaStats:
    """Aggregate filesystem media measurements for one scope."""

    total_files: int
    total_bytes: int
    by_extension: dict[str, int]
    scan_errors: int = 0

    @property
    def average_bytes(self) -> float:
        return self.total_bytes / self.total_files if self.total_files else 0.0


def scan_media(root: Path, guild_id: int | None = None) -> MediaStats:
    """Measure regular media files, excluding symlinks and non-guild folders."""
    breakdown: dict[str, int] = {}
    total_files = 0
    total_bytes = 0
    scan_errors = 0

    if guild_id is not None:
        directories = [root / str(guild_id)]
    else:
        directories = []
        try:
            with os.scandir(root) as entries:
                for entry in entries:
                    try:
                        if entry.name.isdecimal() and entry.is_dir(follow_symlinks=False):
                            directories.append(Path(entry.path))
                    except OSError:
                        scan_errors += 1
        except FileNotFoundError:
            pass
        except OSError:
            scan_errors += 1

    for directory in directories:
        try:
            if directory.is_symlink():
                scan_errors += 1
                continue
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        size = entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        scan_errors += 1
                        continue
                    total_files += 1
                    total_bytes += size
                    raw_extension = Path(entry.name).suffix.lstrip(".").upper()
                    extension = (
                        raw_extension if re.fullmatch(r"[A-Z0-9]{1,10}", raw_extension) else "OTHER"
                    )
                    breakdown[extension] = breakdown.get(extension, 0) + 1
        except FileNotFoundError:
            continue
        except OSError:
            scan_errors += 1

    sorted_breakdown = dict(sorted(breakdown.items(), key=lambda item: (-item[1], item[0])))
    return MediaStats(total_files, total_bytes, sorted_breakdown, scan_errors)


def format_bytes(size: int | float) -> str:
    """Format a non-negative byte count using binary units."""
    if size < 0:
        raise ValueError("byte size cannot be negative")
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    value = float(size)
    for unit in units[:-1]:
        if value < 1024:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} {units[-1]}"


def format_media_summary(stats: MediaStats) -> str:
    """Return the compact value displayed in the Media on Disk field."""
    noun = "file" if stats.total_files == 1 else "files"
    lines = [f"{stats.total_files:,} {noun}"]
    if stats.total_files:
        lines.append(
            f"{format_bytes(stats.total_bytes)} total · "
            f"{format_bytes(stats.average_bytes)}/file avg"
        )
    else:
        lines.append("0 B total")
    if stats.scan_errors:
        noun = "entry" if stats.scan_errors == 1 else "entries"
        lines.append(f"⚠ {stats.scan_errors:,} unreadable {noun}")
    return "\n".join(lines)


def format_media_breakdown(by_extension: dict[str, int], max_length: int = 1024) -> str:
    """Format whole extension/count entries without cutting Markdown mid-token."""
    if max_length < 20:
        raise ValueError("maximum breakdown length must be at least 20")
    entries = [f"**{extension}:** {count:,}" for extension, count in by_extension.items()]
    included: list[str] = []
    for index, entry in enumerate(entries):
        omitted = len(entries) - index - 1
        marker = f"  *+{omitted} more*" if omitted else ""
        candidate = "  ".join([*included, entry])
        if len(candidate) + len(marker) > max_length:
            break
        included.append(entry)
    omitted = len(entries) - len(included)
    value = "  ".join(included)
    if omitted:
        value += f"  *+{omitted} more*"
    return value or "*No media files found*"


def batch_lengths(
    lengths: list[int],
    *,
    max_items: int = 10,
    max_total: int = 6000,
) -> list[tuple[int, int]]:
    """Return half-open ranges that respect Discord collection limits."""
    if max_items < 1 or max_total < 1:
        raise ValueError("batch limits must be positive")
    batches: list[tuple[int, int]] = []
    start = 0
    count = 0
    total = 0
    for index, length in enumerate(lengths):
        if length < 0:
            raise ValueError("item lengths cannot be negative")
        if count and (count >= max_items or total + length > max_total):
            batches.append((start, index))
            start = index
            count = 0
            total = 0
        count += 1
        total += length
    if count:
        batches.append((start, len(lengths)))
    return batches
