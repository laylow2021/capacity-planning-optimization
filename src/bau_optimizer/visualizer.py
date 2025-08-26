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
    
    def visualize_schedule(self, schedule: pd.DataFrame, title: str = "Schedule Analysis") -> go.Figure:
        """
        Create visualization for a single schedule showing resource availability vs needs and gaps.
        
        Args:
            schedule: Schedule DataFrame with activities as rows and months as columns
            title: Title for the visualization
            
        Returns:
            Plotly figure with line plot and heatmap
        """
        # Calculate resource demands and gaps for this schedule
        resource_gaps = self.optimizer.calculate_resource_gaps(schedule)
        
        # Create subplots: line plot on top, heatmap on bottom
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=[
                'Resource Availability vs Demand by Theme',
                'Resource Gaps by Theme'
            ],
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}]],
            vertical_spacing=0.15
        )
        
        # Add line plots for each theme
        for theme in self.optimizer.resource_availability.keys():
            # Available resources (green line)
            fig.add_trace(
                go.Scatter(
                    x=self.month_names,
                    y=self.optimizer.resource_availability[theme],
                    name=f'{theme} - Available',
                    line=dict(color='green', width=2),
                    mode='lines+markers'
                ),
                row=1, col=1
            )
            
            # Resource demand (red line)
            demand = []
            for month in range(1, 13):
                month_demand = sum(
                    schedule.loc[act, month] 
                    for act in self.optimizer.activities.keys() 
                    if self.optimizer.activities[act]['theme'] == theme
                )
                demand.append(month_demand)
            
            fig.add_trace(
                go.Scatter(
                    x=self.month_names,
                    y=demand,
                    name=f'{theme} - Needed',
                    line=dict(color='red', width=2, dash='dash'),
                    mode='lines+markers'
                ),
                row=1, col=1
            )
        
        # Add resource gaps heatmap
        fig.add_trace(
            go.Heatmap(
                z=resource_gaps.values,
                x=self.month_names,
                y=list(resource_gaps.index),
                colorscale='RdYlGn',
                zmid=0,
                name='Resource Gaps',
                colorbar=dict(title="Resource Gap", y=0.25, len=0.4)
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=800,
            title_text=title,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Months", row=1, col=1)
        fig.update_yaxes(title_text="Resource Units", row=1, col=1)
        fig.update_xaxes(title_text="Months", row=2, col=1)
        fig.update_yaxes(title_text="Themes", row=2, col=1)
        
        return fig
