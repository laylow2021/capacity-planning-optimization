# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses a Python virtual environment located at `.venv/`. Always activate the virtual environment before running any commands:

```bash
# Windows Command Prompt
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Unix/MacOS  
source .venv/bin/activate
```

Install dependencies (if not already installed):
```bash
pip install -r requirements.txt
```

**Important**: The notebook and code require packages like numpy, pandas, plotly, etc. that are installed in the `.venv` environment. Make sure to activate the virtual environment before running Jupyter or any Python scripts.

## Running the Code

The main entry point is through the Jupyter notebook:
```bash
jupyter notebook notebooks/bau_optimizer.ipynb
```

To use the optimizer programmatically:
```python
from bau_optimizer import EnhancedBAUOptimizer, BAUVisualizer, ReportGenerator

# Initialize optimizer
optimizer = EnhancedBAUOptimizer()

# Generate schedules
current_schedule = optimizer.generate_current_schedule()
optimized_schedule, changes = optimizer.optimize_schedule()

# Create visualizations
visualizer = BAUVisualizer(optimizer)
fig = visualizer.create_comprehensive_dashboard()

# Generate reports
report_gen = ReportGenerator(optimizer)
summary = report_gen.generate_summary_report()
```

## Testing

The project has a basic test structure in `tests/` directory. To run tests (if pytest is installed):
```bash
python -m pytest tests/
```

## Architecture Overview

### Core Components

- **`EnhancedBAUOptimizer`** (`src/bau_optimizer/core.py:12`): Main optimization engine that uses linear programming principles to minimize resource gaps while respecting priority-based scheduling constraints
- **`BAUVisualizer`** (`src/bau_optimizer/visualizer.py:14`): Creates comprehensive dashboards with heatmaps, gap analysis, and timeline comparisons using Plotly
- **`ConfigManager`** (`src/bau_optimizer/utils.py:12`): Handles configuration loading/saving and validation
- **`ReportGenerator`** (`src/bau_optimizer/utils.py:34`): Generates summary reports and Excel exports

### Key Concepts

**Priority-Based Flexibility**: Activities have different movement constraints:
- High priority: Cannot be moved (0-month window)
- Medium priority: 3-month flexibility window  
- Low priority: 6-month flexibility window

**Resource Theme Management**: Activities are categorized by skill themes (e.g., 'model_ops', 'model_dev') with separate resource availability tracking.

**Optimization Algorithm**: The system identifies resource shortages and attempts to move flexible activities to months with available capacity, minimizing total resource gaps.

### Data Flow

1. Activities are defined with priority, effort, frequency, and theme properties
2. Resource availability is specified per theme and month
3. Current schedule is generated based on original timing and frequency
4. Optimization moves activities within their flexibility windows to minimize gaps
5. Results are visualized and exported for analysis

## Configuration

Activities and resource availability can be customized by passing a config dictionary to `EnhancedBAUOptimizer()`. The default configuration includes OMR (Operational Model Review) activities for various risk models.