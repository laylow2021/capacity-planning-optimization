# Repository Guidelines

## Project Structure & Module Organization
- `src/bau_optimizer/`: core library
  - `core.py`: `EnhancedBAUOptimizer` (scheduling + optimization)
  - `utils.py`: `ConfigManager`, `ReportGenerator` (I/O and reports)
  - `visualizer.py`: `BAUVisualizer` (Plotly/Matplotlib views)
- `tests/`: pytest suites (`test_core.py`, `test_utils.py`, `test_visualizer.py`, edge cases)
- `notebooks/`: exploratory analysis (`bau_optimizer.ipynb`)
- `README.md`: overview and usage

## Build, Test, and Development Commands
- Create venv: `python -m venv .venv && .\.venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt`
  - If missing, install: `pip install numpy pandas scipy matplotlib seaborn plotly openpyxl pytest`
- Run all tests: `pytest -q`
- Run a test subset: `pytest -k optimize_schedule -q`
- Quick run example: `python -c "from src.bau_optimizer.core import EnhancedBAUOptimizer as O;o=O();s,c=o.optimize_schedule();print(s.head())"`

## Coding Style & Naming Conventions
- Follow PEP 8; use 4‑space indentation and type hints where practical.
- Names: modules/functions `snake_case`, classes `CamelCase`, constants `UPPER_SNAKE_CASE`.
- Keep pure, testable functions in `core.py`; avoid side effects in optimization logic.
- Docstrings: concise triple‑quoted summaries with args/returns.

## Testing Guidelines
- Framework: `pytest` with plain asserts.
- Location/patterns: files `tests/test_*.py`, classes `Test*`, methods `test_*`.
- Cover new code paths and edge cases; prefer deterministic tests.
- Run locally with `pytest -q` and target specific tests during iteration (e.g., `pytest tests/test_core.py::TestEnhancedBAUOptimizer::test_optimize_schedule`).

## Commit & Pull Request Guidelines
- Commits: short, imperative, lowercase (e.g., `fix interval calculation`, `add tests`).
- Reference issues when relevant (e.g., `fix scheduler gap #123`).
- PRs: include summary, motivation, before/after notes, tests added/updated, and screenshots for visual changes.
- Keep PRs focused; update docs/examples when behavior changes.

## Security & Configuration Tips (Optional)
- Do not commit secrets or large artifacts; export Excel via `ReportGenerator.export_schedules_to_excel(path)` and share out‑of‑repo.
- Notebook outputs should be cleared before commit; keep data paths configurable.
