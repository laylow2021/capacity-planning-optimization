# src/bau_optimizer/visualizer.py
"""
Visualization components for BAU optimization results.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Tuple, List, Dict


class BAUVisualizer:
    """Visualization utilities for BAU optimization results."""
    
    def __init__(self, optimizer):
        """
        Initialize visualizer with optimizer instance.
        
        Args:
            optimizer: EnhancedBAUOptimizer instance
        """
        self.optimizer = optimizer
        self.month_names = optimizer.month_names
    
    def create_comprehensive_dashboard(self) -> go.Figure:
        """
        Create comprehensive visualization dashboard.
        
        Returns:
            Plotly figure with multiple subplots
        """
        current_schedule = self.optimizer.generate_current_schedule()
        optimized_schedule, changes = self.optimizer.optimize_schedule()
        
        current_gaps = self.optimizer.calculate_resource_gaps(current_schedule)
        optimized_gaps = self.optimizer.calculate_resource_gaps(optimized_schedule)
        
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Current Resource Gaps',
                'Optimized Resource Gaps',
                'Resource Availability by Theme',
                'Schedule Changes Made',
                'Total Gap Comparison',
                'Activity Timeline'
            ],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Add heatmaps for resource gaps
        self._add_gap_heatmaps(fig, current_gaps, optimized_gaps)
        
        # Add resource availability chart
        self._add_resource_availability_chart(fig)
        
        # Add changes summary
        self._add_changes_summary(fig, changes)
        
        # Add gap comparison
        self._add_gap_comparison(fig, current_gaps, optimized_gaps)
        
        # Add activity timeline
        self._add_activity_timeline(fig, current_schedule, optimized_schedule)
        
        fig.update_layout(
            height=1000,
            title_text="BAU Work Optimization Dashboard",
            showlegend=True
        )
        
        return fig
    
    def _add_gap_heatmaps(self, fig: go.Figure, current_gaps: pd.DataFrame, 
                         optimized_gaps: pd.DataFrame) -> None:
        """Add resource gap heatmaps to figure."""
        themes = list(self.optimizer.resource_availability.keys())
        
        fig.add_trace(
            go.Heatmap(
                z=current_gaps.values,
                x=self.month_names,
                y=themes,
                colorscale='RdYlGn',
                zmid=0,
                name='Current Gaps'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Heatmap(
                z=optimized_gaps.values,
                x=self.month_names,
                y=themes,
                colorscale='RdYlGn',
                zmid=0,
                name='Optimized Gaps'
            ),
            row=1, col=2
        )
    
    def _add_resource_availability_chart(self, fig: go.Figure) -> None:
        """Add resource availability chart."""
        for theme, availability in self.optimizer.resource_availability.items():
            fig.add_trace(
                go.Scatter(
                    x=self.month_names,
                    y=availability,
                    name=f'{theme} capacity',
                    mode='lines+markers'
                ),
                row=2, col=1
            )
    
    def _add_changes_summary(self, fig: go.Figure, changes: List[Dict]) -> None:
        """Add changes summary to figure."""
        if changes:
            change_text = '<br>'.join([
                f"{change['activity']}: {self.month_names[change['from_month']-1]} → "
                f"{self.month_names[change['to_month']-1]}"
                for change in changes
            ])
        else:
            change_text = "No changes made"
        
        fig.add_trace(
            go.Scatter(
                x=[0.5], y=[0.5],
                text=[change_text],
                mode='text',
                textposition='middle center',
                showlegend=False
            ),
            row=2, col=2
        )
    
    def _add_gap_comparison(self, fig: go.Figure, current_gaps: pd.DataFrame, 
                           optimized_gaps: pd.DataFrame) -> None:
        """Add gap comparison chart."""
        current_total_gaps = current_gaps.abs().sum()
        optimized_total_gaps = optimized_gaps.abs().sum()
        
        fig.add_trace(
            go.Bar(
                x=self.month_names,
                y=current_total_gaps.values,
                name='Current Total Gaps',
                marker_color='red',
                opacity=0.7
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=self.month_names,
                y=optimized_total_gaps.values,
                name='Optimized Total Gaps',
                marker_color='green',
                opacity=0.7
            ),
            row=3, col=1
        )
    
    def _add_activity_timeline(self, fig: go.Figure, current_schedule: pd.DataFrame, 
                             optimized_schedule: pd.DataFrame) -> None:
        """Add activity timeline comparison."""
        # This would show activity scheduling changes
        # Implementation depends on specific visualization needs
        pass
