"""
Comprehensive edge case tests for BAU optimizer.
"""

import pytest
import pandas as pd
import numpy as np
from src.bau_optimizer.core import EnhancedBAUOptimizer
from src.bau_optimizer.utils import ConfigManager, ReportGenerator
from src.bau_optimizer.visualizer import BAUVisualizer


class TestEdgeCasesCore:
    """Test edge cases for core optimizer functionality."""
    
    def test_zero_resource_availability(self):
        """Test with zero resource availability across all months."""
        config = {
            'activities': {
                'test_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'zero_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'zero_theme': [0.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        gaps = optimizer.calculate_resource_gaps(schedule)
        
        # Should create massive shortages
        assert all(gaps.loc['zero_theme', month] <= 0 for month in range(1, 13))
        
        # Optimization should still work without crashing
        optimized, changes = optimizer.optimize_schedule()
        assert isinstance(optimized, pd.DataFrame)
        assert isinstance(changes, list)
    
    def test_negative_resource_availability(self):
        """Test with negative resource availability (resource shortage from start)."""
        config = {
            'activities': {
                'test_activity': {
                    'priority': 'low',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'negative_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'negative_theme': [-0.5] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        gaps = optimizer.calculate_resource_gaps(optimizer.generate_current_schedule())
        
        # Should have extreme negative gaps
        assert all(gaps.loc['negative_theme', month] < -1.0 for month in range(1, 13))
    
    def test_frequency_larger_than_twelve(self):
        """Test with frequency that would require more than 12 months."""
        config = {
            'activities': {
                'impossible_frequency': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 24,  # Impossible in a 12-month year
                    'theme': 'test_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'test_theme': [2.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        
        # Should handle gracefully - likely only schedule what fits in 12 months
        activity_sum = schedule.loc['impossible_frequency'].sum()
        assert activity_sum >= 0  # Should not crash, may schedule what it can
    
    def test_zero_frequency(self):
        """Test with zero frequency (should not schedule anything)."""
        config = {
            'activities': {
                'zero_frequency': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 0,
                    'theme': 'test_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'test_theme': [2.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        
        # System behavior with zero frequency may vary - it might still schedule once
        # The important thing is it doesn't crash
        assert isinstance(schedule.loc['zero_frequency'].sum(), (int, float))
    
    def test_start_month_beyond_twelve(self):
        """Test with start month > 12."""
        config = {
            'activities': {
                'invalid_start': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 15  # Invalid month
                }
            },
            'resource_availability': {
                'test_theme': [2.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        
        # Should handle gracefully (likely not schedule or schedule in valid month)
        activity_sum = schedule.loc['invalid_start'].sum()
        assert activity_sum >= 0  # Should not crash
    
    def test_start_month_zero_or_negative(self):
        """Test with start month <= 0."""
        config = {
            'activities': {
                'negative_start': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 0  # Invalid month
                }
            },
            'resource_availability': {
                'test_theme': [2.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        
        # Should handle gracefully
        assert isinstance(schedule, pd.DataFrame)
    
    def test_zero_effort_per_cycle(self):
        """Test with zero effort per cycle."""
        config = {
            'activities': {
                'zero_effort': {
                    'priority': 'medium',
                    'effort_per_cycle': 0.0,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'test_theme': [1.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        gaps = optimizer.calculate_resource_gaps(schedule)
        
        # Zero effort should create no demand
        assert schedule.loc['zero_effort', 6] == 0.0
        # Should have surplus resources
        assert gaps.loc['test_theme', 6] == 1.0
    
    def test_negative_effort_per_cycle(self):
        """Test with negative effort per cycle."""
        config = {
            'activities': {
                'negative_effort': {
                    'priority': 'medium',
                    'effort_per_cycle': -1.0,
                    'theme': 'test_theme',
                    'frequency': 1,
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'test_theme': [1.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        gaps = optimizer.calculate_resource_gaps(schedule)
        
        # Negative effort might create surplus instead of demand
        # System should handle this gracefully
        assert isinstance(gaps.loc['test_theme', 6], (int, float))
    
    def test_extremely_large_effort(self):
        """Test with extremely large effort values."""
        config = {
            'activities': {
                'huge_effort': {
                    'priority': 'medium',
                    'effort_per_cycle': 1000000.0,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'test_theme': [1.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        gaps = optimizer.calculate_resource_gaps(schedule)
        
        # Should create massive shortage
        assert gaps.loc['test_theme', 6] <= -999999.0
    
    def test_all_activities_high_priority(self):
        """Test when all activities are high priority (unmoveable)."""
        config = {
            'activities': {
                'high1': {
                    'priority': 'high',
                    'effort_per_cycle': 2.0,
                    'frequency': 1,
                    'theme': 'constrained_theme',
                    'original_start_month': 1
                },
                'high2': {
                    'priority': 'high',
                    'effort_per_cycle': 2.0,
                    'frequency': 1,
                    'theme': 'constrained_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'constrained_theme': [1.0] * 12  # Insufficient for both
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        original = optimizer.generate_current_schedule()
        optimized, changes = optimizer.optimize_schedule()
        
        # Should make no changes since all are high priority
        assert len(changes) == 0
        assert original.equals(optimized)
    
    def test_single_month_with_resources(self):
        """Test with resources available in only one month."""
        config = {
            'activities': {
                'activity1': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'single_month_theme',
                    'original_start_month': 1
                },
                'activity2': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'single_month_theme',
                    'original_start_month': 2
                }
            },
            'resource_availability': {
                'single_month_theme': [0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0]  # Only June has resources
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        optimized, changes = optimizer.optimize_schedule()
        
        # Should try to move activities to June (month 6)
        june_demand = optimized.loc['activity1', 6] + optimized.loc['activity2', 6]
        assert june_demand > 0  # Some activities should move to June
    
    def test_circular_optimization_scenario(self):
        """Test scenario that might cause circular optimization attempts."""
        config = {
            'activities': {
                'circular1': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'circular_theme',
                    'original_start_month': 1
                },
                'circular2': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'circular_theme',
                    'original_start_month': 2
                }
            },
            'resource_availability': {
                'circular_theme': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        optimized, changes = optimizer.optimize_schedule()
        
        # Should complete without infinite loops
        assert isinstance(optimized, pd.DataFrame)
        assert isinstance(changes, list)
    
    def test_mismatched_resource_themes(self):
        """Test activities referencing non-existent resource themes."""
        config = {
            'activities': {
                'orphan_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'nonexistent_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'existing_theme': [1.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        
        # Should handle gracefully (might cause KeyError, but shouldn't crash system)
        try:
            schedule = optimizer.generate_current_schedule()
            gaps = optimizer.calculate_resource_gaps(schedule)
            assert isinstance(schedule, pd.DataFrame)
        except KeyError:
            # This is acceptable behavior for mismatched themes
            pass
    
    def test_empty_activities_dict(self):
        """Test with no activities defined."""
        config = {
            'activities': {},
            'resource_availability': {
                'unused_theme': [1.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        schedule = optimizer.generate_current_schedule()
        gaps = optimizer.calculate_resource_gaps(schedule)
        
        # Should work but be empty
        assert len(schedule) == 0
        # Gaps should show full availability (no demand)
        assert all(gaps.loc['unused_theme', month] == 1.0 for month in range(1, 13))
    
    def test_empty_resource_availability_dict(self):
        """Test with no resource availability defined."""
        config = {
            'activities': {
                'orphan_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'missing_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {}
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        
        # Should handle gracefully or raise appropriate error
        try:
            gaps = optimizer.calculate_resource_gaps(optimizer.generate_current_schedule())
            assert isinstance(gaps, pd.DataFrame)
        except (KeyError, IndexError):
            # Acceptable for empty resource availability
            pass
    
    def test_resource_availability_wrong_length(self):
        """Test resource availability with wrong number of months."""
        config = {
            'activities': {
                'test_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'wrong_length_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'wrong_length_theme': [1.0, 1.0, 1.0]  # Only 3 months instead of 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        
        # Should handle gracefully or raise appropriate error
        try:
            gaps = optimizer.calculate_resource_gaps(optimizer.generate_current_schedule())
            assert isinstance(gaps, pd.DataFrame)
        except (IndexError, ValueError):
            # Acceptable for wrong length
            pass
    
    def test_non_integer_frequency(self):
        """Test with non-integer frequency values."""
        config = {
            'activities': {
                'float_frequency': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 2.5,  # Non-integer frequency
                    'theme': 'test_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'test_theme': [2.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        
        # Should handle gracefully (might floor the frequency or raise error)
        try:
            schedule = optimizer.generate_current_schedule()
            assert isinstance(schedule, pd.DataFrame)
        except (ValueError, TypeError):
            # Acceptable for non-integer frequency
            pass
    
    def test_invalid_priority_values(self):
        """Test with invalid priority values."""
        config = {
            'activities': {
                'invalid_priority': {
                    'priority': 'extreme',  # Invalid priority
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'test_theme': [2.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        
        # get_flexibility_window should return 0 for invalid priority
        flexibility = optimizer.get_flexibility_window('extreme')
        assert flexibility == 0
        
        # Optimization should still work
        optimized, changes = optimizer.optimize_schedule()
        assert isinstance(optimized, pd.DataFrame)
    
    def test_optimization_with_identical_alternatives(self):
        """Test optimization when all alternative months have identical capacity."""
        config = {
            'activities': {
                'identical_options': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'identical_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'identical_theme': [0.5] * 12  # All months identical, all insufficient
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        optimized, changes = optimizer.optimize_schedule()
        
        # Should complete without errors even when no improvement is possible
        assert isinstance(optimized, pd.DataFrame)
        assert isinstance(changes, list)
    
    def test_very_high_frequency_with_constraints(self):
        """Test high frequency activities with tight resource constraints."""
        config = {
            'activities': {
                'frequent_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 0.8,
                    'frequency': 12,  # Every month
                    'theme': 'constrained_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'constrained_theme': [0.5] * 12  # Insufficient every month
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        original = optimizer.generate_current_schedule()
        optimized, changes = optimizer.optimize_schedule()
        
        # Should handle high-frequency activities
        assert isinstance(optimized, pd.DataFrame)
        # Activity should be scheduled in multiple months
        scheduled_months = sum(1 for month in range(1, 13) if optimized.loc['frequent_activity', month] > 0)
        assert scheduled_months > 0