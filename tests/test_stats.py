import pytest

from heisenbot.stats import (
    MediaStats,
    batch_lengths,
    format_bytes,
    format_media_breakdown,
    format_media_summary,
    scan_media,
)


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 B"),
        (1023, "1023 B"),
        (1024, "1.0 KiB"),
        (12 * 1024**2, "12.0 MiB"),
        (12.3 * 1024**3, "12.3 GiB"),
    ],
)
def test_format_bytes(size, expected):
    assert format_bytes(size) == expected


def test_format_media_summary_includes_count_total_and_average():
    stats = MediaStats(
        total_files=1879,
        total_bytes=12 * 1024**3,
        by_extension={"PNG": 1000, "JPG": 879},
    )
    assert format_media_summary(stats) == ("1,879 files\n12.0 GiB total · 6.5 MiB/file avg")


def test_format_media_summary_handles_empty_and_partial_scans():
    stats = MediaStats(total_files=0, total_bytes=0, by_extension={}, scan_errors=2)
    assert format_media_summary(stats) == "0 files\n0 B total\n⚠ 2 unreadable entries"


def test_media_breakdown_keeps_markdown_entries_whole_when_truncated():
    breakdown = {f"TYPE{index}": index for index in range(20)}
    result = format_media_breakdown(breakdown, max_length=80)
    assert len(result) <= 80
    assert "more" in result
    assert result.count("**") % 2 == 0


def test_batch_lengths_honors_item_and_aggregate_limits():
    assert batch_lengths([1000] * 13) == [(0, 6), (6, 12), (12, 13)]
    assert batch_lengths([10] * 21) == [(0, 10), (10, 20), (20, 21)]


def test_invalid_formatting_inputs_are_rejected():
    with pytest.raises(ValueError):
        format_bytes(-1)
    with pytest.raises(ValueError):
        batch_lengths([1], max_items=0)


def test_scan_media_counts_sizes_and_excludes_non_guild_directories_and_symlinks(tmp_path):
    guild = tmp_path / "123"
    guild.mkdir()
    (guild / "one.png").write_bytes(b"1234")
    (guild / "two.JPG").write_bytes(b"123456")
    (guild / "odd.extensiontoolong").write_bytes(b"12")
    (guild / "linked.png").symlink_to(guild / "one.png")
    unrelated = tmp_path / "not-a-guild"
    unrelated.mkdir()
    (unrelated / "ignored.mp4").write_bytes(b"x" * 100)

    stats = scan_media(tmp_path)
    assert stats.total_files == 3
    assert stats.total_bytes == 12
    assert stats.by_extension == {"JPG": 1, "OTHER": 1, "PNG": 1}
    assert stats.scan_errors == 0
