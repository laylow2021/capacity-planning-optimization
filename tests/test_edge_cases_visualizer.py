"""
Edge case tests for visualizer functionality.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from src.bau_optimizer.core import EnhancedBAUOptimizer
from src.bau_optimizer.visualizer import BAUVisualizer


class TestVisualizerEdgeCases:
    """Edge case tests for BAUVisualizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = EnhancedBAUOptimizer()
        self.visualizer = BAUVisualizer(self.optimizer)
    
    def test_visualize_schedule_with_all_zero_values(self):
        """Test visualization with schedule containing all zeros."""
        # Create schedule with all zeros
        zero_schedule = pd.DataFrame(0.0, 
                                   index=self.optimizer.activities.keys(),
                                   columns=self.optimizer.months)
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            # Should not raise an exception
            result = self.visualizer.visualize_schedule(zero_schedule, "Zero Schedule")
            assert result == mock_fig
    
    def test_visualize_schedule_with_negative_values(self):
        """Test visualization with negative schedule values."""
        # Create schedule with negative values (shouldn't normally happen but test edge case)
        negative_schedule = self.optimizer.generate_current_schedule()
        negative_schedule.iloc[0, 0] = -5.0  # Set first activity, first month to negative
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            # Should handle negative values
            result = self.visualizer.visualize_schedule(negative_schedule)
            assert result == mock_fig
    
    def test_visualize_schedule_with_infinite_values(self):
        """Test visualization with infinite schedule values."""
        infinite_schedule = self.optimizer.generate_current_schedule()
        infinite_schedule.iloc[0, 0] = float('inf')
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            try:
                result = self.visualizer.visualize_schedule(infinite_schedule)
                assert result == mock_fig
            except (ValueError, OverflowError):
                # Acceptable to fail with infinite values
                pass
    
    def test_visualize_schedule_with_nan_values(self):
        """Test visualization with NaN schedule values."""
        nan_schedule = self.optimizer.generate_current_schedule()
        nan_schedule.iloc[0, 0] = float('nan')
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            # Should handle NaN values (Plotly usually handles these gracefully)
            result = self.visualizer.visualize_schedule(nan_schedule)
            assert result == mock_fig
    
    def test_visualize_schedule_with_very_large_values(self):
        """Test visualization with extremely large values."""
        large_schedule = self.optimizer.generate_current_schedule()
        large_schedule.iloc[0, 0] = 1e15  # Very large number
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = self.visualizer.visualize_schedule(large_schedule)
            assert result == mock_fig
    
    def test_visualize_schedule_with_single_activity(self):
        """Test visualization with only one activity."""
        config = {
            'activities': {
                'single_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'single_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'single_theme': [2.0] * 12
            }
        }
        
        single_optimizer = EnhancedBAUOptimizer(config)
        single_visualizer = BAUVisualizer(single_optimizer)
        schedule = single_optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = single_visualizer.visualize_schedule(schedule)
            assert result == mock_fig
    
    def test_visualize_schedule_with_single_month_activity(self):
        """Test visualization with activity occurring in only one month."""
        config = {
            'activities': {
                'january_only': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'monthly_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'monthly_theme': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            }
        }
        
        monthly_optimizer = EnhancedBAUOptimizer(config)
        monthly_visualizer = BAUVisualizer(monthly_optimizer)
        schedule = monthly_optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = monthly_visualizer.visualize_schedule(schedule)
            assert result == mock_fig
    
    def test_visualize_schedule_with_wrong_dataframe_structure(self):
        """Test visualization with incorrectly structured DataFrame."""
        # DataFrame with wrong column names
        wrong_columns_schedule = pd.DataFrame(
            0.0,
            index=self.optimizer.activities.keys(),
            columns=['A', 'B', 'C']  # Wrong column names
        )
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            try:
                result = self.visualizer.visualize_schedule(wrong_columns_schedule)
                assert result == mock_fig
            except (KeyError, IndexError):
                # Acceptable to fail with wrong structure
                pass
    
    def test_visualize_schedule_with_empty_dataframe(self):
        """Test visualization with completely empty DataFrame."""
        empty_schedule = pd.DataFrame()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            try:
                result = self.visualizer.visualize_schedule(empty_schedule)
                assert result == mock_fig
            except (KeyError, IndexError, ValueError):
                # Acceptable to fail with empty DataFrame
                pass
    
    def test_visualize_schedule_with_mismatched_index(self):
        """Test visualization with DataFrame having different activities than optimizer."""
        mismatched_schedule = pd.DataFrame(
            0.0,
            index=['nonexistent_activity1', 'nonexistent_activity2'],
            columns=self.optimizer.months
        )
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            try:
                result = self.visualizer.visualize_schedule(mismatched_schedule)
                assert result == mock_fig
            except (KeyError, IndexError):
                # Acceptable to fail with mismatched activities
                pass
    
    def test_visualize_with_optimizer_having_no_resource_themes(self):
        """Test visualization when optimizer has no resource themes."""
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
        
        try:
            empty_resource_optimizer = EnhancedBAUOptimizer(config)
            empty_visualizer = BAUVisualizer(empty_resource_optimizer)
            schedule = empty_resource_optimizer.generate_current_schedule()
            
            with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
                 patch('src.bau_optimizer.visualizer.go') as mock_go:
                
                mock_fig = Mock()
                mock_subplots.return_value = mock_fig
                mock_go.Scatter.return_value = Mock()
                mock_go.Heatmap.return_value = Mock()
                
                result = empty_visualizer.visualize_schedule(schedule)
                assert result == mock_fig
        except (KeyError, IndexError):
            # Acceptable to fail when no resource themes exist
            pass
    
    def test_visualize_with_very_long_activity_names(self):
        """Test visualization with very long activity names."""
        long_name = "very_long_activity_name_" + "x" * 200
        config = {
            'activities': {
                long_name: {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'long_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'long_theme': [2.0] * 12
            }
        }
        
        long_name_optimizer = EnhancedBAUOptimizer(config)
        long_name_visualizer = BAUVisualizer(long_name_optimizer)
        schedule = long_name_optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = long_name_visualizer.visualize_schedule(schedule)
            assert result == mock_fig
    
    def test_visualize_with_special_characters_in_names(self):
        """Test visualization with special characters in activity and theme names."""
        special_config = {
            'activities': {
                'activity@#$%^&*()': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'theme<>?/\\|',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'theme<>?/\\|': [2.0] * 12
            }
        }
        
        special_optimizer = EnhancedBAUOptimizer(special_config)
        special_visualizer = BAUVisualizer(special_optimizer)
        schedule = special_optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = special_visualizer.visualize_schedule(schedule)
            assert result == mock_fig
    
    def test_visualize_with_unicode_characters(self):
        """Test visualization with unicode characters in names."""
        unicode_config = {
            'activities': {
                '活动_测试': {  # Chinese characters
                    'priority': 'médium',  # Accented characters
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'thème_资源',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'thème_资源': [2.0] * 12
            }
        }
        
        unicode_optimizer = EnhancedBAUOptimizer(unicode_config)
        unicode_visualizer = BAUVisualizer(unicode_optimizer)
        schedule = unicode_optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = unicode_visualizer.visualize_schedule(schedule)
            assert result == mock_fig
    
    def test_visualize_with_plotly_import_failure(self):
        """Test behavior when Plotly components fail to import or initialize."""
        schedule = self.optimizer.generate_current_schedule()
        
        # Mock Plotly components to raise exceptions
        with patch('src.bau_optimizer.visualizer.make_subplots', side_effect=ImportError("Plotly not available")):
            with pytest.raises(ImportError):
                self.visualizer.visualize_schedule(schedule)
    
    def test_visualize_with_plotting_exceptions(self):
        """Test visualization when plotting operations raise exceptions."""
        schedule = self.optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.side_effect = ValueError("Invalid plot data")
            
            with pytest.raises(ValueError):
                self.visualizer.visualize_schedule(schedule)
    
    def test_visualize_with_memory_constraints(self):
        """Test visualization with very large datasets that might cause memory issues."""
        # Create a large configuration
        large_activities = {f"activity_{i}": {
            "priority": "medium",
            "effort_per_cycle": 1.0,
            "frequency": 1,
            "theme": "large_theme",
            "original_start_month": (i % 12) + 1
        } for i in range(1000)}  # 1000 activities
        
        large_config = {
            'activities': large_activities,
            'resource_availability': {'large_theme': [1.0] * 12}
        }
        
        large_optimizer = EnhancedBAUOptimizer(large_config)
        large_visualizer = BAUVisualizer(large_optimizer)
        schedule = large_optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            try:
                result = large_visualizer.visualize_schedule(schedule)
                assert result == mock_fig
            except MemoryError:
                # Acceptable to fail with memory constraints
                pass
    
    def test_visualize_concurrent_access(self):
        """Test that multiple visualizers can work simultaneously."""
        config1 = {
            'activities': {'act1': {'priority': 'high', 'effort_per_cycle': 1.0, 
                                  'frequency': 1, 'theme': 'theme1', 'original_start_month': 1}},
            'resource_availability': {'theme1': [1.0] * 12}
        }
        
        config2 = {
            'activities': {'act2': {'priority': 'low', 'effort_per_cycle': 2.0, 
                                  'frequency': 2, 'theme': 'theme2', 'original_start_month': 6}},
            'resource_availability': {'theme2': [0.5] * 12}
        }
        
        optimizer1 = EnhancedBAUOptimizer(config1)
        optimizer2 = EnhancedBAUOptimizer(config2)
        
        visualizer1 = BAUVisualizer(optimizer1)
        visualizer2 = BAUVisualizer(optimizer2)
        
        schedule1 = optimizer1.generate_current_schedule()
        schedule2 = optimizer2.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig1 = Mock()
            mock_fig2 = Mock()
            mock_subplots.side_effect = [mock_fig1, mock_fig2]
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            # Should be able to create visualizations independently
            result1 = visualizer1.visualize_schedule(schedule1, "Config 1")
            result2 = visualizer2.visualize_schedule(schedule2, "Config 2")
            
            assert result1 == mock_fig1
            assert result2 == mock_fig2