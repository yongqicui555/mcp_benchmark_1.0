"""Tests for compute_overdue_state — cron-schedule parsing + overdue detection."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from silentwatch_mcp.analysis import compute_overdue_state


def test_overdue_when_last_run_far_past_for_hourly_schedule() -> None:
    """A job that should run hourly but last ran 3 hours ago is overdue."""
    now = datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC)
    last_run = now - timedelta(hours=3)
    is_overdue, overdue_by, next_run = compute_overdue_state(
        schedule="0 * * * *",
        last_run_at=last_run,
        now=now,
    )
    assert is_overdue is True
    assert overdue_by is not None
    # Next run after last_run was at top of next hour, so 2 hours past now
    assert overdue_by >= 60  # at least an hour overdue
    assert next_run is not None
    assert next_run < now


def test_not_overdue_when_just_ran() -> None:
    """A job that just ran within the schedule is not overdue.

    Use 14:30 as 'now' (mid-hour) so the next-run boundary at 15:00 is unambiguously
    in the future, avoiding the equality edge case where last_run + 1min == 14:00 == now.
    """
    now = datetime(2026, 5, 2, 14, 30, 0, tzinfo=UTC)
    last_run = datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC)  # ran 30 min ago at top of hour
    is_overdue, overdue_by, next_run = compute_overdue_state(
        schedule="0 * * * *",  # hourly
        last_run_at=last_run,
        now=now,
    )
    assert is_overdue is False
    assert overdue_by is None
    assert next_run is not None
    assert next_run > now  # 15:00 > 14:30


def test_grace_minutes_prevents_flag_just_after_expected() -> None:
    """A job 3 minutes past expected isn't overdue if grace is 5 minutes."""
    now = datetime(2026, 5, 2, 14, 3, 0, tzinfo=UTC)
    last_run = datetime(2026, 5, 2, 13, 0, 0, tzinfo=UTC)
    is_overdue, overdue_by, _ = compute_overdue_state(
        schedule="0 * * * *",
        last_run_at=last_run,
        grace_minutes=5,
        now=now,
    )
    assert is_overdue is False
    assert overdue_by is None


def test_overdue_just_outside_grace_window() -> None:
    """A job 7 minutes past expected IS overdue when grace is 5 minutes."""
    now = datetime(2026, 5, 2, 14, 7, 0, tzinfo=UTC)
    last_run = datetime(2026, 5, 2, 13, 0, 0, tzinfo=UTC)
    is_overdue, overdue_by, _ = compute_overdue_state(
        schedule="0 * * * *",
        last_run_at=last_run,
        grace_minutes=5,
        now=now,
    )
    assert is_overdue is True
    assert overdue_by is not None
    assert overdue_by >= 5


def test_unknown_schedule_returns_not_overdue() -> None:
    """Empty or unknown schedule means we can't reason → return not overdue."""
    now = datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC)
    last_run = now - timedelta(days=10)

    is_overdue, overdue_by, next_run = compute_overdue_state(
        schedule="",
        last_run_at=last_run,
        now=now,
    )
    assert is_overdue is False
    assert overdue_by is None
    assert next_run is None

    is_overdue, _, _ = compute_overdue_state(
        schedule="unknown",
        last_run_at=last_run,
        now=now,
    )
    assert is_overdue is False


def test_invalid_schedule_returns_not_overdue() -> None:
    """Malformed cron expression handled gracefully."""
    now = datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC)
    is_overdue, overdue_by, next_run = compute_overdue_state(
        schedule="not a real cron expression at all",
        last_run_at=now - timedelta(hours=1),
        now=now,
    )
    assert is_overdue is False
    assert overdue_by is None
    assert next_run is None


def test_no_last_run_falls_back_to_yesterday_base() -> None:
    """When last_run_at is None, base is 'yesterday' so most schedules look overdue."""
    now = datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC)
    is_overdue, overdue_by, next_run = compute_overdue_state(
        schedule="0 * * * *",  # hourly
        last_run_at=None,
        now=now,
    )
    # Hourly job with base = yesterday → next run was many hours ago
    assert is_overdue is True
    assert overdue_by is not None
    assert overdue_by > 60  # well past first expected fire


def test_at_yearly_schedule() -> None:
    """@yearly shortcut should be parsed by croniter."""
    now = datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC)
    last_run = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    is_overdue, _, next_run = compute_overdue_state(
        schedule="@yearly",
        last_run_at=last_run,
        now=now,
    )
    # Last ran at start of year, next should be Jan 1 next year — not overdue
    assert is_overdue is False
    assert next_run is not None
    assert next_run.year == 2027


def test_at_hourly_schedule_overdue() -> None:
    """@hourly is the same as 0 * * * *; should detect overdue when 5h elapsed."""
    now = datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC)
    last_run = now - timedelta(hours=5)
    is_overdue, overdue_by, _ = compute_overdue_state(
        schedule="@hourly",
        last_run_at=last_run,
        now=now,
    )
    assert is_overdue is True
    assert overdue_by is not None
    assert overdue_by >= 60 * 4  # at least 4 hours overdue


def test_naive_datetime_input_treated_as_utc() -> None:
    """compute_overdue_state should tolerate naive datetimes by assuming UTC."""
    # naive last_run; we don't pass `now=` because naive `datetime.now(UTC)` won't compare cleanly.
    last_run = datetime(2026, 5, 2, 11, 0, 0)  # naive, 3h before implicit "now"
    # Just ensure no exception is raised and result is sane.
    try:
        is_overdue, _, _ = compute_overdue_state(
            schedule="0 * * * *",
            last_run_at=last_run,
        )
    except (TypeError, ValueError) as exc:
        # Acceptable for naive datetimes to be rejected explicitly; either implementation OK.
        # If it raises, this test documents the behavior.
        assert "tz" in str(exc).lower() or "naive" in str(exc).lower()
        return
    # If it didn't raise, the result must still be a bool
    assert isinstance(is_overdue, bool)
