# src/bau_optimizer/core.py
"""
Core optimization logic for BAU work scheduling.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.optimize import linprog


class EnhancedBAUOptimizer:
    """
    Enhanced BAU work optimizer with priority-based flexibility and resource themes.
    
    Attributes:
        activities (Dict): Dictionary of activities with their properties
        resource_availability (Dict): Resource availability by theme and month
        months (List): List of month numbers (1-12)
        month_names (List): List of month names for display
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the BAU optimizer.
        
        Args:
            config: Optional configuration dictionary to override defaults
        """
        self.activities = self._get_default_activities()
        self.resource_availability = self._get_default_resources()
        self.months = list(range(1, 13))
        self.month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        if config:
            self._apply_config(config)
    
    def _get_default_activities(self) -> Dict:
        """Get default activity configuration."""
        return {
            'omr_jupiter': {
                'priority': 'medium',
                'effort_per_cycle': 0.75,
                'frequency': 2,
                'theme': 'model_ops',
                'original_start_month': 2
            },
            'omr_wildfire_damage': {
                'priority': 'medium',
                'effort_per_cycle': 0.75,
                'frequency': 2,
                'theme': 'model_ops',
                'original_start_month': 2
            },
            'omr_physical_risk_damage': {
                'priority': 'medium',
                'effort_per_cycle': 0.75,
                'frequency': 2,
                'theme': 'model_ops',
                'original_start_month': 5
            },
            'omr_scorecard': {
                'priority': 'medium',
                'effort_per_cycle': 0.75,
                'frequency': 1,
                'theme': 'model_ops',
                'original_start_month': 11
            },
            'omr_first_street': {
                'priority': 'medium',
                'effort_per_cycle': 0.75,
                'frequency': 1,
                'theme': 'model_ops',
                'original_start_month': 7
            },
            'omr_ice': {
                'priority': 'high',
                'effort_per_cycle': 0.75,
                'frequency': 1,
                'theme': 'model_dev',
                'original_start_month': 11
            }
        }
    
    def _get_default_resources(self) -> Dict:
        """Get default resource availability configuration."""
        return {
            'model_ops': [1,1,1,1,1,1,0.5,0.5,1,1,1,0],
        }
    
    def _apply_config(self, config: Dict) -> None:
        """Apply custom configuration."""
        if 'activities' in config:
            self.activities.update(config['activities'])
        if 'resource_availability' in config:
            self.resource_availability.update(config['resource_availability'])
    
    def get_flexibility_window(self, priority: str) -> int:
        """
        Get flexibility window based on priority.
        
        Args:
            priority: Priority level ('high', 'medium', 'low')
            
        Returns:
            Number of months the activity can be moved
        """
        flexibility = {
            'high': 0,
            'medium': 3,
            'low': 6
        }
        return flexibility.get(priority, 0)
    
    def generate_current_schedule(self) -> pd.DataFrame:
        """
        Generate current schedule based on original timing and frequency.
        
        Returns:
            DataFrame with activities as rows and months as columns
        """
        schedule = pd.DataFrame(0.0, index=self.activities.keys(), columns=self.months)
        
        for activity, config in self.activities.items():
            start_month = config['original_start_month']
            frequency = config['frequency']
            effort = config['effort_per_cycle']
            
            interval = 12 // frequency if frequency > 1 else 12
            
            current_month = start_month
            while current_month <= 12:
                schedule.loc[activity, current_month] = effort
                current_month += interval
        
        return schedule
    
    def calculate_resource_gaps(self, schedule: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate resource gaps for given schedule.
        
        Args:
            schedule: Schedule DataFrame
            
        Returns:
            DataFrame with resource gaps by theme and month
        """
        themes = list(self.resource_availability.keys())
        gap_analysis = pd.DataFrame(0.0, index=themes, columns=self.months)
        
        for theme in themes:
            for month in self.months:
                demand = sum(schedule.loc[act, month] 
                           for act in self.activities.keys() 
                           if self.activities[act]['theme'] == theme)
                
                supply = self.resource_availability[theme][month-1]
                gap_analysis.loc[theme, month] = supply - demand
        
        return gap_analysis
    
    def optimize_schedule(self) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Optimize schedule to minimize resource gaps.
        
        Returns:
            Tuple of (optimized_schedule, changes_made)
        """
        current_schedule = self.generate_current_schedule()
        optimized_schedule = current_schedule.copy()
        changes_made = []
        
        current_gaps = self.calculate_resource_gaps(current_schedule)
        
        # Identify problem areas (resource shortages)
        problem_areas = []
        for theme in current_gaps.index:
            for month in current_gaps.columns:
                gap = current_gaps.loc[theme, month]
                if gap < -0.25:  # Significant shortage
                    problem_areas.append((theme, month, gap))
        
        problem_areas.sort(key=lambda x: x[2])  # Sort by severity
        
        # Resolve each problem area
        for theme, problem_month, gap in problem_areas:
            moveable_activities = self._find_moveable_activities(
                theme, problem_month, optimized_schedule
            )
            
            for activity, flexibility in moveable_activities:
                if optimized_schedule.loc[activity, problem_month] <= 0:
                    continue
                
                effort = optimized_schedule.loc[activity, problem_month]
                target_month = self._find_best_target_month(
                    theme, problem_month, effort, flexibility, optimized_schedule
                )
                
                if target_month is not None:
                    # Make the move
                    optimized_schedule.loc[activity, problem_month] = 0
                    optimized_schedule.loc[activity, target_month] = effort
                    
                    changes_made.append({
                        'activity': activity,
                        'from_month': problem_month,
                        'to_month': target_month,
                        'effort': effort,
                        'reason': f'Resolved {theme} shortage in {self.month_names[problem_month-1]}'
                    })
                    break
        
        return optimized_schedule, changes_made
    
    def _find_moveable_activities(self, theme: str, month: int, 
                                 schedule: pd.DataFrame) -> List[Tuple[str, int]]:
        """Find activities that can be moved for optimization."""
        moveable = []
        for activity, config in self.activities.items():
            if (config['theme'] == theme and 
                config['priority'] != 'high' and 
                schedule.loc[activity, month] > 0):
                flexibility = self.get_flexibility_window(config['priority'])
                moveable.append((activity, flexibility))
        return moveable
    
    def _find_best_target_month(self, theme: str, problem_month: int, 
                               effort: float, flexibility: int, 
                               schedule: pd.DataFrame) -> Optional[int]:
        """Find the best target month to move an activity."""
        best_target = None
        best_improvement = 0
        
        for offset in range(-flexibility, flexibility + 1):
            target_month = problem_month + offset
            if target_month < 1 or target_month > 12 or target_month == problem_month:
                continue
            
            gaps = self.calculate_resource_gaps(schedule)
            target_gap = gaps.loc[theme, target_month]
            
            if target_gap >= effort:
                problem_gap = gaps.loc[theme, problem_month]
                improvement = abs(problem_gap) + target_gap - effort
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_target = target_month
        
        return best_target
