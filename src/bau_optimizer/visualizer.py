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
