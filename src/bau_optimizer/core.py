# src/bau_optimizer/core.py
"""
Core optimization logic for BAU work scheduling.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


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
        # Replace defaults with provided config for predictable behavior in tests and usage
        if 'activities' in config:
            self.activities = dict(config['activities'])
        if 'resource_availability' in config:
            # Merge non-empty themes with defaults; if empty dict provided, replace
            ra = config['resource_availability']
            if ra:
                merged = dict(self.resource_availability)
                merged.update(ra)
                self.resource_availability = merged
            else:
                self.resource_availability = {}
    
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
            'medium': 6,
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
            start_month = int(config.get('original_start_month', 1))
            raw_frequency = config.get('frequency', 1)
            try:
                frequency = int(raw_frequency)
            except (TypeError, ValueError):
                frequency = 0
            effort = config.get('effort_per_cycle', 0.0)

            if frequency <= 0:
                # Undefined or zero frequency -> do not schedule occurrences
                continue

            # Normalize start month to [1, 12]
            start_month = max(1, min(12, start_month))

            # Determine interval; avoid zero step and handle very high freq
            if frequency == 1:
                interval = 12
            elif frequency >= 12:
                interval = 1
            else:
                interval = max(1, 12 // frequency)

            for m in range(start_month, 13, interval):
                schedule.loc[activity, m] = effort
        
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
        Optimize schedule to minimize resource gaps while preserving fixed intervals.
        
        Returns:
            Tuple of (optimized_schedule, changes_made)
        """
        current_schedule = self.generate_current_schedule()
        optimized_schedule = current_schedule.copy()
        changes_made = []

        max_iterations = 10
        for _ in range(max_iterations):
            changes_in_pass = 0

            current_gaps = self.calculate_resource_gaps(optimized_schedule)

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
                # Skip if this month is no longer a problem in the current optimized schedule
                current_gaps_live = self.calculate_resource_gaps(optimized_schedule)
                if current_gaps_live.loc[theme, problem_month] >= -0.25:
                    continue
                moveable_activities = self._find_moveable_activities(
                    theme, problem_month, optimized_schedule
                )

                for activity, flexibility in moveable_activities:

                    # Get activity configuration
                    activity_config = self.activities[activity]
                    try:
                        frequency = int(activity_config.get('frequency', 1))
                    except (TypeError, ValueError):
                        frequency = 0

                    if frequency > 1:
                        # For activities with frequency > 1, move entire activity set
                        success = self._move_activity_set(
                            activity, optimized_schedule, flexibility, theme
                        )
                        if success:
                            # Get original and new dates
                            orig_start, orig_end = self._get_activity_dates(activity, current_schedule)
                            new_start, new_end = self._get_activity_dates(activity, optimized_schedule)

                            changes_made.append({
                                'activity': activity,
                                'from_month': orig_start,
                                'to_month': new_start,
                                'effort': activity_config.get('effort_per_cycle', 0.0),
                                'reason': f'Moved entire activity set to resolve {theme} shortage',
                                'original_start_month': orig_start,
                                'original_end_month': orig_end,
                                'new_start_month': new_start,
                                'new_end_month': new_end,
                                'frequency': frequency
                            })
                            changes_in_pass += 1
                            break
                    else:
                        # For single occurrence activities, use original logic
                        effort = optimized_schedule.loc[activity, problem_month]
                        if effort <= 0:
                            continue
                        target_month = self._find_best_target_month(
                            theme, problem_month, effort, flexibility, optimized_schedule
                        )

                        if target_month is not None:
                            # Get original dates before making the move
                            orig_start, orig_end = self._get_activity_dates(activity, current_schedule)

                            # Make the move
                            optimized_schedule.loc[activity, problem_month] = 0
                            optimized_schedule.loc[activity, target_month] = effort

                            # Get new dates after making the move
                            new_start, new_end = self._get_activity_dates(activity, optimized_schedule)

                            changes_made.append({
                                'activity': activity,
                                'from_month': problem_month,
                                'to_month': target_month,
                                'effort': effort,
                                'reason': f'Resolved {theme} shortage in {self.month_names[problem_month-1]}',
                                'original_start_month': orig_start,
                                'original_end_month': orig_end,
                                'new_start_month': new_start,
                                'new_end_month': new_end,
                                'frequency': frequency
                            })
                            changes_in_pass += 1
                            break

            if changes_in_pass == 0:
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

        gaps = self.calculate_resource_gaps(schedule)
        problem_gap = gaps.loc[theme, problem_month]

        for offset in range(-flexibility, flexibility + 1):
            target_month = problem_month + offset
            if target_month < 1 or target_month > 12 or target_month == problem_month:
                continue

            target_gap = gaps.loc[theme, target_month]

            if target_gap >= effort:
                improvement = abs(problem_gap) + target_gap - effort
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_target = target_month

        return best_target
    
    def _move_activity_set(self, activity: str, schedule: pd.DataFrame, 
                          flexibility: int, theme: str) -> bool:
        """
        Move an entire activity set while preserving fixed intervals.
        
        Args:
            activity: Activity name
            schedule: Schedule DataFrame to modify
            flexibility: Number of months the activity can be moved
            theme: Resource theme for gap calculation
            
        Returns:
            True if move was successful, False otherwise
        """
        activity_config = self.activities[activity]
        frequency = activity_config['frequency']
        effort = activity_config['effort_per_cycle']
        interval = 12 // frequency
        
        # Find current activity months
        current_months = [month for month in range(1, 13) if schedule.loc[activity, month] > 0]
        if not current_months:
            return False
        
        current_start = min(current_months)
        
        # Try different start months within flexibility window
        best_start = None
        best_improvement = -float('inf')

        # Calculate gaps once for the current schedule state
        gaps = self.calculate_resource_gaps(schedule)

        for offset in range(-flexibility, flexibility + 1):
            new_start = current_start + offset
            if new_start < 1 or new_start > 12:
                continue
            
            # Calculate new occurrence months
            new_months = []
            month = new_start
            for _ in range(frequency):
                if month <= 12:
                    new_months.append(month)
                    month += interval
            
            # Skip if any occurrence falls outside the year
            if len(new_months) != frequency:
                continue
            
            # Check if all target months have sufficient capacity
            can_move = True
            total_improvement = 0
            
            for new_month in new_months:
                available_gap = gaps.loc[theme, new_month]
                if new_month not in current_months and available_gap < effort:
                    can_move = False
                    break
                # Calculate improvement (reduction in absolute gaps)
                if new_month in current_months:
                    total_improvement += 0  # No change for this month
                else:
                    total_improvement += available_gap - effort
            
            # Add improvement from clearing current months
            for curr_month in current_months:
                if curr_month not in new_months:
                    curr_gap = gaps.loc[theme, curr_month]
                    total_improvement += abs(curr_gap) - abs(curr_gap + effort)
            
            if can_move and total_improvement > best_improvement:
                best_improvement = total_improvement
                best_start = new_start
        
        # Apply the best move if found
        if best_start is not None:
            # Clear current schedule for this activity
            schedule.loc[activity, :] = 0

            # Set new schedule
            month = best_start
            for _ in range(frequency):
                if month <= 12:
                    schedule.loc[activity, month] = effort
                    month += interval
            
            return True
        
        return False
    
    def _get_activity_dates(self, activity: str, schedule: pd.DataFrame) -> Tuple[Optional[int], Optional[int]]:
        """
        Get start and end months for an activity in a schedule.
        
        Args:
            activity: Activity name
            schedule: Schedule DataFrame
            
        Returns:
            Tuple of (start_month, end_month) or (None, None) if activity not scheduled
        """
        activity_months = schedule.loc[activity]
        active_months = [month for month in activity_months.index if activity_months[month] > 0]
        
        if not active_months:
            return None, None
        
        return min(active_months), max(active_months)
    
    def validate_schedule_intervals(self, schedule: pd.DataFrame) -> bool:
        """
        Validate that all activities with frequency > 1 maintain their required intervals.
        
        Args:
            schedule: Schedule DataFrame to validate
            
        Returns:
            True if all intervals are valid, False otherwise
        """
        for activity, config in self.activities.items():
            try:
                frequency = int(config.get('frequency', 1))
            except (TypeError, ValueError):
                frequency = 0
            if frequency <= 1:
                continue
            
            expected_interval = 1 if frequency >= 12 else max(1, 12 // frequency)
            activity_months = [month for month in range(1, 13) if schedule.loc[activity, month] > 0]
            
            if len(activity_months) != frequency:
                return False
            
            # Check intervals between consecutive occurrences
            for i in range(1, len(activity_months)):
                actual_interval = activity_months[i] - activity_months[i-1]
                if actual_interval != expected_interval:
                    return False
        
        return True
