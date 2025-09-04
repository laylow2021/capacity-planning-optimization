"""
Tests for the BAU optimizer package initialization.
"""

import pytest
from src.bau_optimizer import EnhancedBAUOptimizer, BAUVisualizer, ConfigManager, ReportGenerator


class TestPackageInit:
    """Test cases for package initialization and imports."""
    
    def test_imports_available(self):
        """Test that all main classes can be imported from package."""
        # Should be able to import all main classes
        assert EnhancedBAUOptimizer is not None
        assert BAUVisualizer is not None
        assert ConfigManager is not None
        assert ReportGenerator is not None
    
    def test_classes_are_callable(self):
        """Test that imported classes can be instantiated."""
        # Should be able to create instances
        optimizer = EnhancedBAUOptimizer()
        assert optimizer is not None
        
        visualizer = BAUVisualizer(optimizer)
        assert visualizer is not None
        
        # ConfigManager has static methods, no need to instantiate
        assert hasattr(ConfigManager, 'load_config')
        assert hasattr(ConfigManager, 'save_config')
        assert hasattr(ConfigManager, 'validate_config')
        
        report_gen = ReportGenerator(optimizer)
        assert report_gen is not None
    
    def test_class_types(self):
        """Test that imported classes have correct types."""
        optimizer = EnhancedBAUOptimizer()
        visualizer = BAUVisualizer(optimizer)
        report_gen = ReportGenerator(optimizer)
        
        assert isinstance(optimizer, EnhancedBAUOptimizer)
        assert isinstance(visualizer, BAUVisualizer)
        assert isinstance(report_gen, ReportGenerator)
    
    def test_integration_basic_workflow(self):
        """Test basic integration workflow using imported classes."""
        # Test that the classes work together
        optimizer = EnhancedBAUOptimizer()
        
        # Generate schedules
        current_schedule = optimizer.generate_current_schedule()
        optimized_schedule, changes = optimizer.optimize_schedule()
        
        # Create visualizer
        visualizer = BAUVisualizer(optimizer)
        
        # Create report generator
        report_gen = ReportGenerator(optimizer)
        summary = report_gen.generate_summary_report()
        
        # All should work without errors
        assert current_schedule is not None
        assert optimized_schedule is not None
        assert isinstance(changes, list)
        assert isinstance(summary, dict)
        assert 'current_gaps_total' in summary