# src/bau_optimizer/utils.py
"""
Utility functions and helpers for BAU optimization.
"""

import json
import pandas as pd
from typing import Dict, Any
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
        
        # Calculate metrics
        current_total_gap = abs(current_gaps.values).sum()
        optimized_total_gap = abs(optimized_gaps.values).sum()
        improvement_pct = ((current_total_gap - optimized_total_gap) / 
                          current_total_gap) * 100 if current_total_gap > 0 else 0
        
        return {
            'current_gaps_total': float(current_total_gap),
            'optimized_gaps_total': float(optimized_total_gap),
            'improvement_percent': float(improvement_pct),
            'changes_made': len(changes),
            'changes_detail': changes,
            'resource_themes': list(self.optimizer.resource_availability.keys()),
            'total_activities': len(self.optimizer.activities)
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
