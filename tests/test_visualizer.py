"""
Tests for the BAU visualizer functionality.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.bau_optimizer.core import EnhancedBAUOptimizer
from src.bau_optimizer.visualizer import BAUVisualizer


class TestBAUVisualizer:
    """Test cases for BAUVisualizer class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.optimizer = EnhancedBAUOptimizer()
        self.visualizer = BAUVisualizer(self.optimizer)
    
    def test_initialization(self):
        """Test visualizer initialization."""
        assert self.visualizer.optimizer == self.optimizer
        assert self.visualizer.month_names == self.optimizer.month_names
        assert len(self.visualizer.month_names) == 12
    
    @patch('src.bau_optimizer.visualizer.make_subplots')
    @patch('src.bau_optimizer.visualizer.go')
    def test_visualize_schedule_structure(self, mock_go, mock_make_subplots):
        """Test that visualize_schedule creates the correct plot structure."""
        # Mock the figure and traces
        mock_fig = Mock()
        mock_make_subplots.return_value = mock_fig
        
        # Mock scatter and heatmap trace constructors
        mock_scatter = Mock()
        mock_heatmap = Mock()
        mock_go.Scatter.return_value = mock_scatter
        mock_go.Heatmap.return_value = mock_heatmap
        
        schedule = self.optimizer.generate_current_schedule()
        result = self.visualizer.visualize_schedule(schedule, "Test Schedule")
        
        # Check that subplots were created with correct parameters
        mock_make_subplots.assert_called_once()
        call_kwargs = mock_make_subplots.call_args[1]
        assert call_kwargs['rows'] == 2
        assert call_kwargs['cols'] == 1
        assert 'Resource Availability vs Demand by Theme' in call_kwargs['subplot_titles']
        assert 'Resource Gaps by Theme' in call_kwargs['subplot_titles']
        
        # Check that traces were added (scatter plots for availability/demand + heatmap)
        expected_calls = len(self.optimizer.resource_availability) * 2 + 1  # 2 lines per theme + 1 heatmap
        assert mock_fig.add_trace.call_count == expected_calls
        
        # Check that layout was updated
        mock_fig.update_layout.assert_called_once()
        layout_kwargs = mock_fig.update_layout.call_args[1]
        assert layout_kwargs['height'] == 800
        assert layout_kwargs['title_text'] == "Test Schedule"
        assert layout_kwargs['showlegend'] is True
        
        # Check that axes were updated
        assert mock_fig.update_xaxes.call_count == 2  # Two subplots
        assert mock_fig.update_yaxes.call_count == 2  # Two subplots
        
        assert result == mock_fig
    
    @patch('src.bau_optimizer.visualizer.go')
    def test_visualize_schedule_data_accuracy(self, mock_go):
        """Test that visualize_schedule uses correct data."""
        # Create a simple test case with known values
        config = {
            'activities': {
                'test_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 3
                }
            },
            'resource_availability': {
                'test_theme': [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 
                              2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        visualizer = BAUVisualizer(optimizer)
        schedule = optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots:
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            
            # Mock trace constructors to capture their arguments
            mock_scatter_calls = []
            mock_heatmap_calls = []
            
            def capture_scatter(**kwargs):
                mock_scatter_calls.append(kwargs)
                return Mock()
            
            def capture_heatmap(**kwargs):
                mock_heatmap_calls.append(kwargs)
                return Mock()
            
            mock_go.Scatter.side_effect = capture_scatter
            mock_go.Heatmap.side_effect = capture_heatmap
            
            visualizer.visualize_schedule(schedule, "Test")
            
            # Check availability line data
            availability_calls = [call for call in mock_scatter_calls 
                                if 'Available' in call.get('name', '')]
            # Should have one availability line per theme (original optimizer has model_ops + test_theme)
            assert len(availability_calls) == 2
            # Find the test_theme availability call
            test_theme_calls = [call for call in availability_calls 
                               if 'test_theme' in call.get('name', '')]
            assert len(test_theme_calls) == 1
            availability_call = test_theme_calls[0]
            assert availability_call['y'] == config['resource_availability']['test_theme']
            
            # Check demand line data  
            demand_calls = [call for call in mock_scatter_calls 
                          if 'Needed' in call.get('name', '')]
            assert len(demand_calls) == 2  # One for each theme
            # Find the test_theme demand call
            test_theme_demand_calls = [call for call in demand_calls 
                                     if 'test_theme' in call.get('name', '')]
            assert len(test_theme_demand_calls) == 1
            demand_call = test_theme_demand_calls[0]
            # Demand should be [0,0,1,0,0,0,0,0,0,0,0,0] since activity is in month 3
            expected_demand = [0.0] * 12
            expected_demand[2] = 1.0  # Month 3 (index 2)
            assert demand_call['y'] == expected_demand
            
            # Check heatmap data
            assert len(mock_heatmap_calls) == 1
            heatmap_call = mock_heatmap_calls[0]
            assert 'z' in heatmap_call
            assert 'x' in heatmap_call
            assert 'y' in heatmap_call
    
    def test_visualize_schedule_with_empty_schedule(self):
        """Test visualizer with empty schedule."""
        empty_schedule = pd.DataFrame(0.0, 
                                    index=self.optimizer.activities.keys(), 
                                    columns=self.optimizer.months)
        
        # Should not raise an exception
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = self.visualizer.visualize_schedule(empty_schedule)
            assert result == mock_fig
    
    def test_visualize_schedule_default_title(self):
        """Test that default title is used when none provided."""
        schedule = self.optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            self.visualizer.visualize_schedule(schedule)
            
            # Check that default title was used
            layout_call = mock_fig.update_layout.call_args[1]
            assert layout_call['title_text'] == "Schedule Analysis"
    
    def test_visualize_schedule_multiple_themes(self):
        """Test visualizer with multiple resource themes."""
        config = {
            'activities': {
                'activity1': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'theme1',
                    'original_start_month': 1
                },
                'activity2': {
                    'priority': 'medium',
                    'effort_per_cycle': 0.5,
                    'frequency': 1,
                    'theme': 'theme2',
                    'original_start_month': 2
                }
            },
            'resource_availability': {
                'theme1': [1.5] * 12,
                'theme2': [1.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        visualizer = BAUVisualizer(optimizer)
        schedule = optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            visualizer.visualize_schedule(schedule)
            
            # Should have 2 themes × 2 lines each = 4 scatter plots + 1 heatmap = 5 traces
            # But the custom optimizer might have the original themes too, so we need to be flexible
            expected_traces = len(optimizer.resource_availability) * 2 + 1
            assert mock_fig.add_trace.call_count == expected_traces
    
    @patch('src.bau_optimizer.visualizer.go')
    def test_visualize_schedule_trace_properties(self, mock_go):
        """Test that traces have correct styling properties."""
        schedule = self.optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots:
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            
            mock_scatter_calls = []
            mock_heatmap_calls = []
            
            def capture_scatter(**kwargs):
                mock_scatter_calls.append(kwargs)
                return Mock()
            
            def capture_heatmap(**kwargs):
                mock_heatmap_calls.append(kwargs)
                return Mock()
            
            mock_go.Scatter.side_effect = capture_scatter
            mock_go.Heatmap.side_effect = capture_heatmap
            
            self.visualizer.visualize_schedule(schedule)
            
            # Check scatter plot properties
            for call in mock_scatter_calls:
                assert 'x' in call
                assert 'y' in call
                assert 'name' in call
                assert 'line' in call
                assert 'mode' in call
                assert call['mode'] == 'lines+markers'
                
                # Check line styling
                line_props = call['line']
                assert 'width' in line_props
                assert line_props['width'] == 2
                
                # Available resources should be green, demand should be red
                if 'Available' in call['name']:
                    assert line_props['color'] == 'green'
                elif 'Needed' in call['name']:
                    assert line_props['color'] == 'red'
                    assert 'dash' in line_props
                    assert line_props['dash'] == 'dash'
            
            # Check heatmap properties
            assert len(mock_heatmap_calls) == 1
            heatmap_call = mock_heatmap_calls[0]
            assert heatmap_call['colorscale'] == 'RdYlGn'
            assert heatmap_call['zmid'] == 0
            assert 'colorbar' in heatmap_call
            colorbar = heatmap_call['colorbar']
            assert colorbar['title'] == "Resource Gap"
    
    def test_visualizer_with_custom_optimizer(self):
        """Test visualizer works with custom optimizer configurations."""
        custom_config = {
            'activities': {
                'custom_activity': {
                    'priority': 'low',
                    'effort_per_cycle': 2.5,
                    'frequency': 3,
                    'theme': 'custom_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'custom_theme': [3.0] * 12
            }
        }
        
        custom_optimizer = EnhancedBAUOptimizer(custom_config)
        visualizer = BAUVisualizer(custom_optimizer)
        
        assert visualizer.optimizer == custom_optimizer
        assert visualizer.month_names == custom_optimizer.month_names
        
        # Should be able to visualize custom schedule without errors
        schedule = custom_optimizer.generate_current_schedule()
        
        with patch('src.bau_optimizer.visualizer.make_subplots') as mock_subplots, \
             patch('src.bau_optimizer.visualizer.go') as mock_go:
            
            mock_fig = Mock()
            mock_subplots.return_value = mock_fig
            mock_go.Scatter.return_value = Mock()
            mock_go.Heatmap.return_value = Mock()
            
            result = visualizer.visualize_schedule(schedule, "Custom Test")
            assert result == mock_fig