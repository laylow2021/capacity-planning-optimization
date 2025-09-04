import sys
from pathlib import Path

# Ensure src is on path for imports when running tests from repo root
BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bau_optimizer.core import EnhancedBAUOptimizer  # noqa: E402


def months_with_activity(schedule, activity):
    row = schedule.loc[activity]
    return [m for m in row.index if row[m] > 0]


def total_shortage(gaps_df):
    # Sum of negative gaps (as positive magnitudes)
    return float((-gaps_df[gaps_df < 0]).fillna(0).sum().sum())


def test_generate_current_schedule_intervals():
    opt = EnhancedBAUOptimizer()
    sched = opt.generate_current_schedule()

    # Validate interval for a known biannual task
    activity = "omr_jupiter"
    freq = opt.activities[activity]["frequency"]
    interval = 12 // freq
    months = months_with_activity(sched, activity)

    assert len(months) == freq
    assert all((months[i] - months[i - 1]) == interval for i in range(1, len(months)))


def test_calculate_resource_gaps_dimensions():
    opt = EnhancedBAUOptimizer()
    sched = opt.generate_current_schedule()
    gaps = opt.calculate_resource_gaps(sched)

    assert list(gaps.columns) == opt.months
    assert set(gaps.index) == set(opt.resource_availability.keys())


def test_optimize_preserves_intervals():
    opt = EnhancedBAUOptimizer()
    sched = opt.generate_current_schedule()
    optimized, _ = opt.optimize_schedule()

    assert opt.validate_schedule_intervals(optimized)


def test_high_priority_not_moved():
    opt = EnhancedBAUOptimizer()
    current = opt.generate_current_schedule()
    optimized, _ = opt.optimize_schedule()

    # High priority activity should not be moved
    activity = "omr_ice"
    assert months_with_activity(current, activity) == months_with_activity(optimized, activity)


def test_shortage_not_worse_after_optimization():
    opt = EnhancedBAUOptimizer()
    current = opt.generate_current_schedule()
    base_gaps = opt.calculate_resource_gaps(current)
    optimized, _ = opt.optimize_schedule()
    opt_gaps = opt.calculate_resource_gaps(optimized)

    assert total_shortage(opt_gaps) <= total_shortage(base_gaps) + 1e-9

