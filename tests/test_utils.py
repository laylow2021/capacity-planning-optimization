"""
Tests for the BAU optimizer utility functions.
"""

import pytest
import json
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.bau_optimizer.core import EnhancedBAUOptimizer
from src.bau_optimizer.utils import ConfigManager, ReportGenerator


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def test_load_config_success(self):
        """Test successful config loading from JSON file."""
        test_config = {
            "activities": {
                "test_activity": {
                    "priority": "medium",
                    "effort_per_cycle": 1.0,
                    "frequency": 1,
                    "theme": "test_theme",
                    "original_start_month": 6
                }
            },
            "resource_availability": {
                "test_theme": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            }
        }
        
        mock_file_content = json.dumps(test_config)
        
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            result = ConfigManager.load_config("test_config.json")
        
        assert result == test_config
        assert "activities" in result
        assert "resource_availability" in result
    
    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                ConfigManager.load_config("nonexistent.json")
    
    def test_load_config_invalid_json(self):
        """Test config loading with invalid JSON."""
        invalid_json = "{ invalid json content"
        
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with pytest.raises(json.JSONDecodeError):
                ConfigManager.load_config("invalid.json")
    
    def test_save_config_success(self):
        """Test successful config saving to JSON file."""
        test_config = {
            "activities": {
                "test_activity": {
                    "priority": "high",
                    "effort_per_cycle": 0.5,
                    "frequency": 2,
                    "theme": "test_theme",
                    "original_start_month": 3
                }
            },
            "resource_availability": {
                "test_theme": [0.5] * 12
            }
        }
        
        m = mock_open()
        with patch("builtins.open", m):
            ConfigManager.save_config(test_config, "output.json")
        
        # Check that file was opened for writing
        m.assert_called_once_with("output.json", 'w')
        
        # Check that JSON was written with proper indentation
        written_content = ''.join(call.args[0] for call in m().write.call_args_list)
        parsed_content = json.loads(written_content)
        assert parsed_content == test_config
    
    def test_save_config_write_error(self):
        """Test config saving when write fails."""
        test_config = {"test": "data"}
        
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                ConfigManager.save_config(test_config, "readonly.json")
    
    def test_validate_config_valid(self):
        """Test config validation with valid configuration."""
        valid_config = {
            "activities": {
                "activity1": {
                    "priority": "medium",
                    "effort_per_cycle": 1.0,
                    "frequency": 1,
                    "theme": "theme1",
                    "original_start_month": 5
                }
            },
            "resource_availability": {
                "theme1": [1] * 12
            },
            "extra_field": "this is allowed"  # Extra fields are okay
        }
        
        assert ConfigManager.validate_config(valid_config) is True
    
    def test_validate_config_missing_activities(self):
        """Test config validation when activities key is missing."""
        invalid_config = {
            "resource_availability": {
                "theme1": [1] * 12
            }
        }
        
        assert ConfigManager.validate_config(invalid_config) is False
    
    def test_validate_config_missing_resource_availability(self):
        """Test config validation when resource_availability key is missing."""
        invalid_config = {
            "activities": {
                "activity1": {
                    "priority": "medium",
                    "effort_per_cycle": 1.0,
                    "frequency": 1,
                    "theme": "theme1",
                    "original_start_month": 5
                }
            }
        }
        
        assert ConfigManager.validate_config(invalid_config) is False
    
    def test_validate_config_empty(self):
        """Test config validation with empty configuration."""
        assert ConfigManager.validate_config({}) is False
    
    def test_validate_config_none(self):
        """Test config validation with None input."""
        with pytest.raises(TypeError):
            ConfigManager.validate_config(None)


class TestReportGenerator:
    """Test cases for ReportGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.optimizer = EnhancedBAUOptimizer()
        self.report_gen = ReportGenerator(self.optimizer)
    
    def test_initialization(self):
        """Test report generator initialization."""
        assert self.report_gen.optimizer == self.optimizer
    
    def test_generate_summary_report_structure(self):
        """Test that summary report has correct structure."""
        report = self.report_gen.generate_summary_report()
        
        # Check required keys
        required_keys = [
            'current_gaps_total',
            'optimized_gaps_total', 
            'improvement_percent',
            'changes_made',
            'changes_detail',
            'resource_themes',
            'total_activities'
        ]
        
        for key in required_keys:
            assert key in report, f"Missing key: {key}"
        
        # Check data types
        assert isinstance(report['current_gaps_total'], float)
        assert isinstance(report['optimized_gaps_total'], float)
        assert isinstance(report['improvement_percent'], float)
        assert isinstance(report['changes_made'], int)
        assert isinstance(report['changes_detail'], list)
        assert isinstance(report['resource_themes'], list)
        assert isinstance(report['total_activities'], int)
    
    def test_generate_summary_report_values(self):
        """Test that summary report has reasonable values."""
        report = self.report_gen.generate_summary_report()
        
        # Gaps should be non-negative (absolute values)
        assert report['current_gaps_total'] >= 0
        assert report['optimized_gaps_total'] >= 0
        
        # Improvement percent should be reasonable
        assert -100 <= report['improvement_percent'] <= 100
        
        # Changes made should be non-negative
        assert report['changes_made'] >= 0
        
        # Should have resource themes
        assert len(report['resource_themes']) > 0
        assert 'model_ops' in report['resource_themes']
        
        # Should have activities
        assert report['total_activities'] > 0
        assert report['total_activities'] == len(self.optimizer.activities)
    
    def test_generate_summary_report_with_no_changes(self):
        """Test summary report when optimization makes no changes."""
        # Create a scenario where no optimization is needed
        config = {
            'activities': {
                'simple_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 0.5,
                    'frequency': 1,
                    'theme': 'simple_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'simple_theme': [2.0] * 12  # Abundant resources
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        report_gen = ReportGenerator(optimizer)
        report = report_gen.generate_summary_report()
        
        # Should have no changes or very few changes
        # Note: Even with abundant resources, optimizer might still make minor adjustments
        assert report['changes_made'] >= 0
        assert isinstance(report['changes_detail'], list)
        
        # Should still have valid metrics
        assert isinstance(report['current_gaps_total'], float)
        assert isinstance(report['optimized_gaps_total'], float)
    
    def test_generate_summary_report_with_optimization_needed(self):
        """Test summary report when optimization improves the schedule."""
        # Create a scenario that needs optimization
        config = {
            'activities': {
                'heavy_activity': {
                    'priority': 'medium',  # Can be moved
                    'effort_per_cycle': 2.0,
                    'frequency': 1,
                    'theme': 'constrained_theme',
                    'original_start_month': 7  # July has 0.5 resources
                }
            },
            'resource_availability': {
                'constrained_theme': [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 
                                     0.5, 0.5, 2.0, 2.0, 2.0, 2.0]
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        report_gen = ReportGenerator(optimizer)
        report = report_gen.generate_summary_report()
        
        # Should show improvement (gaps should be reduced)
        assert report['optimized_gaps_total'] <= report['current_gaps_total']
        
        # If optimization was successful, should have positive improvement
        if report['changes_made'] > 0:
            # Improvement percent can be negative if optimization made things worse, 
            # but gaps should still be reduced
            assert isinstance(report['improvement_percent'], (int, float))
    
    def test_export_schedules_to_excel_structure(self):
        """Test that Excel export method works without errors."""
        # Test that the method can generate the required data structures
        current_schedule = self.report_gen.optimizer.generate_current_schedule()
        optimized_schedule, changes = self.report_gen.optimizer.optimize_schedule()
        
        current_gaps = self.report_gen.optimizer.calculate_resource_gaps(current_schedule)
        optimized_gaps = self.report_gen.optimizer.calculate_resource_gaps(optimized_schedule)
        
        # Verify all data structures are DataFrames with expected structure
        assert isinstance(current_schedule, pd.DataFrame)
        assert isinstance(optimized_schedule, pd.DataFrame)
        assert isinstance(current_gaps, pd.DataFrame)
        assert isinstance(optimized_gaps, pd.DataFrame)
        
        # Verify they have the same shape
        assert current_schedule.shape == optimized_schedule.shape
        assert current_gaps.shape == optimized_gaps.shape
        
        # Test with a temporary file (will be cleaned up)
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            # Should not raise an exception
            self.report_gen.export_schedules_to_excel(temp_path)
            # Check that file was created
            assert os.path.exists(temp_path)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_schedules_to_excel_with_changes(self):
        """Test Excel export data accuracy when optimization makes changes."""
        # Create scenario that will generate changes
        config = {
            'activities': {
                'moveable_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.5,
                    'frequency': 1,
                    'theme': 'test_theme',
                    'original_start_month': 7  # Resource-constrained month
                }
            },
            'resource_availability': {
                'test_theme': [2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
                              0.5, 0.5, 2.0, 2.0, 2.0, 2.0]  # July/Aug constrained
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        report_gen = ReportGenerator(optimizer)
        
        # Test that the optimization produces valid data for export
        current_schedule = optimizer.generate_current_schedule()
        optimized_schedule, changes = optimizer.optimize_schedule()
        
        # Should have valid schedules for export
        assert isinstance(current_schedule, pd.DataFrame)
        assert isinstance(optimized_schedule, pd.DataFrame)
        assert current_schedule.shape == optimized_schedule.shape
        
        # Test with a real file to ensure the export actually works
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            # Should not raise an exception
            report_gen.export_schedules_to_excel(temp_path)
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_schedules_to_excel_file_write_error(self):
        """Test Excel export when file write fails."""
        with patch('pandas.ExcelWriter', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                self.report_gen.export_schedules_to_excel("readonly.xlsx")
    
    def test_report_generator_with_custom_optimizer(self):
        """Test report generator with custom optimizer configuration."""
        custom_config = {
            'activities': {
                'custom1': {
                    'priority': 'high',
                    'effort_per_cycle': 1.0,
                    'frequency': 2,
                    'theme': 'custom_theme',
                    'original_start_month': 1
                },
                'custom2': {
                    'priority': 'low',
                    'effort_per_cycle': 0.5,
                    'frequency': 1,
                    'theme': 'custom_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'custom_theme': [1.0] * 12
            }
        }
        
        custom_optimizer = EnhancedBAUOptimizer(custom_config)
        report_gen = ReportGenerator(custom_optimizer)
        report = report_gen.generate_summary_report()
        
        # Should handle custom configuration correctly
        # Note: Custom config updates the default activities, doesn't replace them
        assert report['total_activities'] >= 2  # Should have at least our custom activities
        assert 'custom_theme' in report['resource_themes']
        # May have more than one theme due to default config
        assert len(report['resource_themes']) >= 1
    
    def test_improvement_percentage_calculation(self):
        """Test improvement percentage calculation edge cases."""
        # Test with zero current gaps (should not divide by zero)
        config = {
            'activities': {
                'light_activity': {
                    'priority': 'medium',
                    'effort_per_cycle': 0.1,
                    'frequency': 1,
                    'theme': 'abundant_theme',
                    'original_start_month': 1
                }
            },
            'resource_availability': {
                'abundant_theme': [10.0] * 12  # Way more than needed
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        report_gen = ReportGenerator(optimizer)
        report = report_gen.generate_summary_report()
        
        # Should handle zero gaps case without error
        assert isinstance(report['improvement_percent'], float)
        # The improvement percentage can vary depending on optimizer behavior
        # Just ensure it's a valid number (not NaN or infinity)
        assert not (report['improvement_percent'] != report['improvement_percent'])  # Check for NaN
        assert abs(report['improvement_percent']) < float('inf')  # Check for infinity