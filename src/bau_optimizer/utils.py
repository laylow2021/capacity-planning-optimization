# src/bau_optimizer/utils.py
"""
Utility functions and helpers for BAU optimization.
"""

import json
import pandas as pd
from typing import Dict, Any, Iterable
from pathlib import Path


class ConfigManager:
    """Configuration management utilities."""
    
    @staticmethod
    def load_config(file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_config(config: Dict[str, Any], file_path: str) -> None:
        """Save configuration to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        required_keys = ['activities', 'resource_availability']
        return all(key in config for key in required_keys)


class ReportGenerator:
    """Generate reports from optimization results."""
    
    def __init__(self, optimizer):
        """Initialize with optimizer instance."""
        self.optimizer = optimizer
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of optimization results."""
        current_schedule = self.optimizer.generate_current_schedule()
        optimized_schedule, changes = self.optimizer.optimize_schedule()
        
        current_gaps = self.optimizer.calculate_resource_gaps(current_schedule)
        optimized_gaps = self.optimizer.calculate_resource_gaps(optimized_schedule)

        # Consider only themes used by activities when possible
        try:
            used_themes = {cfg.get('theme') for cfg in self.optimizer.activities.values()}
        except Exception:
            used_themes = set()
        def select_used_themes(gaps_obj):
            try:
                if hasattr(gaps_obj, 'loc') and hasattr(gaps_obj, 'index') and used_themes:
                    present = [t for t in used_themes if t in gaps_obj.index]
                    return gaps_obj.loc[present] if present else gaps_obj
            except Exception:
                pass
            return gaps_obj

        current_gaps_sel = select_used_themes(current_gaps)
        optimized_gaps_sel = select_used_themes(optimized_gaps)

        def total_abs(values_obj) -> float:
            # Support pandas/numpy objects, plain lists, and mocks exposing `.values`
            try:
                values = getattr(values_obj, 'values', values_obj)
                if hasattr(values, 'tolist'):
                    values = values.tolist()
            except Exception:
                values = values_obj

            def flatten(x: Iterable):
                for el in x:
                    if isinstance(el, (list, tuple)):
                        for sub in flatten(el):
                            yield sub
                    else:
                        yield el

            total = 0.0
            for v in flatten(values if isinstance(values, (list, tuple)) else [values]):
                try:
                    total += abs(float(v))
                except Exception:
                    # Skip non-numeric entries
                    continue
            return float(total)
        
        # Calculate metrics
        current_total_gap = total_abs(current_gaps_sel)
        optimized_total_gap = total_abs(optimized_gaps_sel)
        improvement_pct = ((current_total_gap - optimized_total_gap) / 
                          current_total_gap) * 100 if current_total_gap > 0 else 0
        
        # Count total scheduled occurrences in current schedule
        try:
            total_activities = len(self.optimizer.activities)
        except Exception:
            total_activities = 0

        try:
            ra = self.optimizer.resource_availability
            resource_themes = list(ra.keys()) if isinstance(ra, dict) else []
        except Exception:
            resource_themes = []

        return {
            'current_gaps_total': float(current_total_gap),
            'optimized_gaps_total': float(optimized_total_gap),
            'improvement_percent': float(improvement_pct),
            'changes_made': len(changes),
            'changes_detail': changes,
            'resource_themes': resource_themes,
            'total_activities': total_activities
        }
    
    def export_schedules_to_excel(self, file_path: str) -> None:
        """Export current and optimized schedules to Excel."""
        current_schedule = self.optimizer.generate_current_schedule()
        optimized_schedule, changes = self.optimizer.optimize_schedule()
        
        current_gaps = self.optimizer.calculate_resource_gaps(current_schedule)
        optimized_gaps = self.optimizer.calculate_resource_gaps(optimized_schedule)
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            current_schedule.to_excel(writer, sheet_name='Current_Schedule')
            optimized_schedule.to_excel(writer, sheet_name='Optimized_Schedule')
            current_gaps.to_excel(writer, sheet_name='Current_Gaps')
            optimized_gaps.to_excel(writer, sheet_name='Optimized_Gaps')
            
            if changes:
                changes_df = pd.DataFrame(changes)
                changes_df.to_excel(writer, sheet_name='Changes_Made', index=False)
