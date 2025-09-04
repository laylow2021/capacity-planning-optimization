"""
Tests for the core BAU optimizer functionality.
"""

import pytest
import pandas as pd
import numpy as np
from src.bau_optimizer.core import EnhancedBAUOptimizer


class TestEnhancedBAUOptimizer:
    """Test cases for EnhancedBAUOptimizer class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.optimizer = EnhancedBAUOptimizer()
    
    def test_initialization(self):
        """Test optimizer initialization with default config."""
        assert isinstance(self.optimizer.activities, dict)
        assert isinstance(self.optimizer.resource_availability, dict)
        assert self.optimizer.months == list(range(1, 13))
        assert len(self.optimizer.month_names) == 12
        assert 'omr_jupiter' in self.optimizer.activities
    
    def test_initialization_with_custom_config(self):
        """Test optimizer initialization with custom config."""
        custom_config = {
            'activities': {
                'test_activity': {
                    'priority': 'high',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'test_theme': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            }
        }
        optimizer = EnhancedBAUOptimizer(custom_config)
        assert 'test_activity' in optimizer.activities
        assert 'test_theme' in optimizer.resource_availability
        assert optimizer.activities['test_activity']['priority'] == 'high'
    
    def test_get_flexibility_window(self):
        """Test flexibility window calculation based on priority."""
        assert self.optimizer.get_flexibility_window('high') == 0
        assert self.optimizer.get_flexibility_window('medium') == 3
        assert self.optimizer.get_flexibility_window('low') == 6
        assert self.optimizer.get_flexibility_window('invalid') == 0
    
    def test_generate_current_schedule(self):
        """Test current schedule generation."""
        schedule = self.optimizer.generate_current_schedule()
        
        # Check DataFrame structure
        assert isinstance(schedule, pd.DataFrame)
        assert list(schedule.columns) == self.optimizer.months
        assert set(schedule.index) == set(self.optimizer.activities.keys())
        
        # Check specific activities are scheduled correctly
        # omr_jupiter should be in Feb (2) and Aug (8) with frequency 2
        assert schedule.loc['omr_jupiter', 2] > 0
        assert schedule.loc['omr_jupiter', 8] > 0
        assert schedule.loc['omr_jupiter', 5] == 0  # Should not be in May
        
        # omr_scorecard should be only in Nov (11) with frequency 1
        assert schedule.loc['omr_scorecard', 11] > 0
        assert schedule.loc['omr_scorecard', 6] == 0  # Should not be in June
    
    def test_calculate_resource_gaps(self):
        """Test resource gap calculation."""
        schedule = self.optimizer.generate_current_schedule()
        gaps = self.optimizer.calculate_resource_gaps(schedule)
        
        # Check DataFrame structure
        assert isinstance(gaps, pd.DataFrame)
        assert list(gaps.columns) == self.optimizer.months
        assert set(gaps.index) == set(self.optimizer.resource_availability.keys())
        
        # Check gap calculations are reasonable (positive means surplus, negative means shortage)
        # Values should be numeric
        assert all(isinstance(val, (int, float)) for val in gaps.values.flatten())
    
    def test_optimize_schedule(self):
        """Test schedule optimization."""
        original_schedule = self.optimizer.generate_current_schedule()
        optimized_schedule, changes = self.optimizer.optimize_schedule()
        
        # Check return types
        assert isinstance(optimized_schedule, pd.DataFrame)
        assert isinstance(changes, list)
        
        # Check optimized schedule has same structure
        assert optimized_schedule.shape == original_schedule.shape
        assert list(optimized_schedule.columns) == list(original_schedule.columns)
        assert set(optimized_schedule.index) == set(original_schedule.index)
        
        # Check changes structure if any were made
        for change in changes:
            assert 'activity' in change
            assert 'from_month' in change or 'original_start_month' in change
            assert 'to_month' in change or 'new_start_month' in change
            assert 'effort' in change
            assert 'reason' in change
    
    def test_find_moveable_activities(self):
        """Test finding moveable activities for optimization."""
        schedule = self.optimizer.generate_current_schedule()
        
        # Test with model_ops theme and a month where activities exist
        moveable = self.optimizer._find_moveable_activities('model_ops', 2, schedule)
        
        assert isinstance(moveable, list)
        # Each item should be a tuple of (activity_name, flexibility)
        for item in moveable:
            assert isinstance(item, tuple)
            assert len(item) == 2
            activity, flexibility = item
            assert isinstance(activity, str)
            assert isinstance(flexibility, int)
            # Activity should be moveable (not high priority)
            assert self.optimizer.activities[activity]['priority'] != 'high'
    
    def test_find_best_target_month(self):
        """Test finding best target month for activity movement."""
        schedule = self.optimizer.generate_current_schedule()
        
        # Test moving an activity with medium priority (flexibility = 3)
        target = self.optimizer._find_best_target_month(
            'model_ops', 2, 0.75, 3, schedule
        )
        
        # Should return None or a valid month number
        if target is not None:
            assert isinstance(target, int)
            assert 1 <= target <= 12
            assert target != 2  # Should not return the same month
    
    def test_get_activity_dates(self):
        """Test getting start and end dates for activities."""
        schedule = self.optimizer.generate_current_schedule()
        
        # Test with omr_jupiter which should have multiple occurrences
        start, end = self.optimizer._get_activity_dates('omr_jupiter', schedule)
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert 1 <= start <= 12
        assert 1 <= end <= 12
        assert start <= end
        
        # Test with an activity that might not be scheduled
        empty_schedule = pd.DataFrame(0.0, index=self.optimizer.activities.keys(), columns=self.optimizer.months)
        start, end = self.optimizer._get_activity_dates('omr_jupiter', empty_schedule)
        assert start is None
        assert end is None
    
    def test_validate_schedule_intervals(self):
        """Test schedule interval validation."""
        # Test with valid current schedule
        schedule = self.optimizer.generate_current_schedule()
        assert self.optimizer.validate_schedule_intervals(schedule) is True
        
        # Test with invalid schedule (wrong intervals)
        invalid_schedule = schedule.copy()
        # Break the interval for omr_jupiter (should be every 6 months)
        invalid_schedule.loc['omr_jupiter', 2] = 0  # Remove Feb
        invalid_schedule.loc['omr_jupiter', 3] = 0.75  # Add March (wrong interval)
        
        assert self.optimizer.validate_schedule_intervals(invalid_schedule) is False
    
    def test_move_activity_set(self):
        """Test moving an entire activity set while preserving intervals."""
        schedule = self.optimizer.generate_current_schedule()
        original_schedule = schedule.copy()
        
        # Test moving omr_jupiter (frequency 2, should maintain 6-month interval)
        success = self.optimizer._move_activity_set('omr_jupiter', schedule, 3, 'model_ops')
        
        assert isinstance(success, bool)
        
        if success:
            # Check that intervals are still valid
            assert self.optimizer.validate_schedule_intervals(schedule)
            
            # Check that the activity was actually moved (schedule changed)
            jupiter_orig = original_schedule.loc['omr_jupiter']
            jupiter_new = schedule.loc['omr_jupiter']
            # At least one month should be different
            assert not jupiter_orig.equals(jupiter_new)
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with minimal config
        minimal_config = {
            'activities': {
                'single_activity': {
                    'priority': 'low',
                    'effort_per_cycle': 0.5,
                    'frequency': 1,
                    'theme': 'single_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'single_theme': [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 
                               0.25, 0.25, 0.25, 0.25, 0.25, 0.25]
            }
        }
        
        optimizer = EnhancedBAUOptimizer(minimal_config)
        schedule = optimizer.generate_current_schedule()
        gaps = optimizer.calculate_resource_gaps(schedule)
        
        # Should have resource shortage
        assert gaps.loc['single_theme', 1] < 0
        
        # Optimization should try to help
        optimized, changes = optimizer.optimize_schedule()
        assert isinstance(optimized, pd.DataFrame)
        assert isinstance(changes, list)
    
    def test_high_priority_activities_not_moved(self):
        """Test that high priority activities are never moved during optimization."""
        # Add a high priority activity that causes resource shortage
        config = {
            'activities': {
                'high_priority_test': {
                    'priority': 'high',
                    'effort_per_cycle': 2.0,  # High effort to cause shortage
                    'frequency': 1,
                    'theme': 'model_ops',
                    'original_start_month': 7  # July (low resource month)
                }
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        original_schedule = optimizer.generate_current_schedule()
        optimized_schedule, changes = optimizer.optimize_schedule()
        
        # High priority activity should not move
        assert (original_schedule.loc['high_priority_test'] == 
                optimized_schedule.loc['high_priority_test']).all()
        
        # No changes should involve the high priority activity
        high_priority_changes = [c for c in changes if c['activity'] == 'high_priority_test']
        assert len(high_priority_changes) == 0
    
    def test_resource_themes_isolation(self):
        """Test that different resource themes are handled independently."""
        config = {
            'activities': {
                'theme1_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'theme1',
                    'original_start_month': 1
                },
                'theme2_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'theme2',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'theme1': [0.5] * 12,  # Shortage
                'theme2': [2.0] * 12   # Surplus
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        gaps = optimizer.calculate_resource_gaps(optimizer.generate_current_schedule())
        
        # Theme1 should have shortage, Theme2 should have surplus
        assert gaps.loc['theme1', 1] < 0
        assert gaps.loc['theme2', 1] > 0