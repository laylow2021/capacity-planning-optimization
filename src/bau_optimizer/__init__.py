# src/bau_optimizer/__init__.py
"""
BAU Work Optimization Utility

A Python utility for optimizing Business-As-Usual work allocation using 
linear programming with priority-based scheduling flexibility.
"""

from .core import EnhancedBAUOptimizer
from .visualizer import BAUVisualizer
from .utils import ConfigManager, ReportGenerator

__version__ = "0.1.0"
__author__ = "TZ"
__email__ = "nemozt@gmail.com"

__all__ = [
    "EnhancedBAUOptimizer",
    "BAUVisualizer", 
    "ConfigManager",
    "ReportGenerator"
]
