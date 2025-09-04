import time
from pathlib import Path
import sys

# Ensure src on path when running from repo root
BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bau_optimizer.core import EnhancedBAUOptimizer  # noqa: E402


def main(runs: int = 50):
    opt = EnhancedBAUOptimizer()

    # Warm-up
    opt.optimize_schedule()

    t0 = time.perf_counter()
    for _ in range(runs):
        opt.optimize_schedule()
    t1 = time.perf_counter()

    avg_ms = (t1 - t0) * 1000.0 / runs
    print(f"Runs: {runs}")
    print(f"Average optimize_schedule(): {avg_ms:.3f} ms")


if __name__ == "__main__":
    runs = 50
    if len(sys.argv) > 1:
        try:
            runs = int(sys.argv[1])
        except ValueError:
            pass
    main(runs)

