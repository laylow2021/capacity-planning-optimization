"""
Edge case tests for utility functions.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from src.bau_optimizer.core import EnhancedBAUOptimizer
from src.bau_optimizer.utils import ConfigManager, ReportGenerator


class TestConfigManagerEdgeCases:
    """Edge case tests for ConfigManager."""
    
    def test_load_config_empty_file(self):
        """Test loading an empty JSON file."""
        with patch("builtins.open", mock_open(read_data="")):
            with pytest.raises(json.JSONDecodeError):
                ConfigManager.load_config("empty.json")
    
    def test_load_config_non_json_file(self):
        """Test loading a non-JSON file."""
        non_json_content = "This is not JSON content\nIt's just plain text"
        with patch("builtins.open", mock_open(read_data=non_json_content)):
            with pytest.raises(json.JSONDecodeError):
                ConfigManager.load_config("text.json")
    
    def test_load_config_malformed_json(self):
        """Test loading malformed JSON with various syntax errors."""
        malformed_cases = [
            '{"key": "value",}',  # Trailing comma
            '{"key": "value"',    # Missing closing brace
            '{"key": }',          # Missing value
            '{key: "value"}',     # Unquoted key
            '{"key": "value" "another": "value"}',  # Missing comma
        ]
        
        for malformed_json in malformed_cases:
            with patch("builtins.open", mock_open(read_data=malformed_json)):
                with pytest.raises(json.JSONDecodeError):
                    ConfigManager.load_config("malformed.json")
    
    def test_save_config_to_readonly_directory(self):
        """Test saving config to a read-only directory."""
        config = {"test": "data"}
        
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                ConfigManager.save_config(config, "/readonly/config.json")
    
    def test_save_config_to_nonexistent_directory(self):
        """Test saving config to non-existent directory path."""
        config = {"test": "data"}
        
        with patch("builtins.open", side_effect=FileNotFoundError("Directory not found")):
            with pytest.raises(FileNotFoundError):
                ConfigManager.save_config(config, "/nonexistent/path/config.json")
    
    def test_save_config_disk_full(self):
        """Test saving config when disk is full."""
        config = {"test": "data"}
        
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            with pytest.raises(OSError):
                ConfigManager.save_config(config, "config.json")
    
    def test_save_config_with_non_serializable_data(self):
        """Test saving config with non-JSON-serializable data."""
        # Functions are not JSON serializable
        config = {
            "function": lambda x: x,
            "set": {1, 2, 3},
            "complex": complex(1, 2)
        }
        
        m = mock_open()
        with patch("builtins.open", m):
            with pytest.raises(TypeError):
                ConfigManager.save_config(config, "config.json")
    
    def test_validate_config_with_wrong_data_types(self):
        """Test config validation with wrong data types."""
        invalid_configs = [
            {"activities": "not_a_dict", "resource_availability": {}},
            {"activities": [], "resource_availability": {}},
            {"activities": {}, "resource_availability": "not_a_dict"},
            {"activities": {}, "resource_availability": []},
            {"activities": None, "resource_availability": {}},
            {"activities": {}, "resource_availability": None},
        ]
        
        for config in invalid_configs:
            # Should still return True since we only check for key presence
            assert ConfigManager.validate_config(config) is True
    
    def test_validate_config_with_nested_invalid_structure(self):
        """Test config validation with valid top-level but invalid nested structure."""
        config = {
            "activities": {
                "invalid_activity": "this should be a dict"
            },
            "resource_availability": {
                "theme1": "this should be a list"
            }
        }
        
        # Current validation only checks top-level keys
        assert ConfigManager.validate_config(config) is True
    
    def test_validate_config_with_unicode_characters(self):
        """Test config validation with unicode characters."""
        config = {
            "activities": {
                "活动_test": {  # Chinese characters
                    "priority": "médium",  # Accented characters
                    "theme": "thème_测试"  # Mixed unicode
                }
            },
            "resource_availability": {
                "thème_测试": [1.0] * 12
            }
        }
        
        assert ConfigManager.validate_config(config) is True
    
    def test_load_config_with_very_large_file(self):
        """Test loading a very large config file."""
        # Create a large config structure
        large_activities = {f"activity_{i}": {
            "priority": "medium",
            "effort_per_cycle": 1.0,
            "frequency": 1,
            "theme": f"theme_{i % 10}",
            "original_start_month": (i % 12) + 1
        } for i in range(10000)}
        
        large_config = {
            "activities": large_activities,
            "resource_availability": {f"theme_{i}": [1.0] * 12 for i in range(10)}
        }
        
        large_json = json.dumps(large_config)
        
        with patch("builtins.open", mock_open(read_data=large_json)):
            result = ConfigManager.load_config("large.json")
            assert len(result["activities"]) == 10000
            assert len(result["resource_availability"]) == 10


class TestReportGeneratorEdgeCases:
    """Edge case tests for ReportGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = EnhancedBAUOptimizer()
        self.report_gen = ReportGenerator(self.optimizer)
    
    def test_generate_report_with_all_zero_gaps(self):
        """Test report generation when all gaps are exactly zero."""
        config = {
            'activities': {
                'perfect_match': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'perfect_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'perfect_theme': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]  # Exactly 1 in June
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        report_gen = ReportGenerator(optimizer)
        report = report_gen.generate_summary_report()
        
        # Should handle zero gaps without division by zero
        assert report['current_gaps_total'] == 0.0
        assert report['optimized_gaps_total'] == 0.0
        assert report['improvement_percent'] == 0.0  # Should be 0, not NaN
    
    def test_generate_report_with_optimization_makes_things_worse(self):
        """Test report when optimization actually makes gaps worse."""
        # This is a tricky scenario to create, but we can mock it
        original_optimizer = self.report_gen.optimizer
        mock_optimizer = Mock()
        mock_optimizer.generate_current_schedule.return_value = Mock()
        mock_optimizer.optimize_schedule.return_value = (Mock(), [])
        mock_optimizer.calculate_resource_gaps.side_effect = [
            Mock(values=[[1.0]]),  # Current gaps (small)
            Mock(values=[[5.0]])   # Optimized gaps (larger)
        ]
        
        self.report_gen.optimizer = mock_optimizer
        
        try:
            report = self.report_gen.generate_summary_report()
            # Improvement percent should be negative
            assert report['improvement_percent'] < 0
        finally:
            self.report_gen.optimizer = original_optimizer
    
    def test_generate_report_with_infinite_gaps(self):
        """Test report generation with extremely large gap values."""
        config = {
            'activities': {
                'massive_activity': {
                    'priority': 'high',
                    'effort_per_cycle': float('inf'),  # Infinite effort
                    'frequency': 1,
                    'theme': 'finite_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'finite_theme': [1.0] * 12
            }
        }
        
        try:
            optimizer = EnhancedBAUOptimizer(config)
            report_gen = ReportGenerator(optimizer)
            report = report_gen.generate_summary_report()
            
            # Should handle infinite values gracefully
            assert isinstance(report['current_gaps_total'], (int, float))
            assert isinstance(report['improvement_percent'], (int, float))
        except (OverflowError, ValueError):
            # Acceptable to raise error for infinite values
            pass
    
    def test_generate_report_with_nan_gaps(self):
        """Test report generation with NaN gap values."""
        # Mock optimizer to return NaN values
        original_optimizer = self.report_gen.optimizer
        mock_optimizer = Mock()
        mock_optimizer.generate_current_schedule.return_value = Mock()
        mock_optimizer.optimize_schedule.return_value = (Mock(), [])
        mock_optimizer.calculate_resource_gaps.side_effect = [
            Mock(values=[[float('nan')]]),  # Current gaps (NaN)
            Mock(values=[[1.0]])            # Optimized gaps (normal)
        ]
        
        self.report_gen.optimizer = mock_optimizer
        
        try:
            report = self.report_gen.generate_summary_report()
            # Should handle NaN values
            assert isinstance(report['current_gaps_total'], (int, float))
        finally:
            self.report_gen.optimizer = original_optimizer
    
    def test_export_to_excel_with_empty_changes(self):
        """Test Excel export when there are no changes made."""
        # Use optimizer that won't make changes
        config = {
            'activities': {
                'unmoveable': {
                    'priority': 'high',  # Can't be moved
                    'effort_per_cycle': 0.5,
                    'frequency': 1,
                    'theme': 'abundant_theme',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'abundant_theme': [10.0] * 12  # Abundant resources
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        report_gen = ReportGenerator(optimizer)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            # Should work even with no changes
            report_gen.export_schedules_to_excel(temp_path)
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_excel_with_very_long_activity_names(self):
        """Test Excel export with very long activity names."""
        long_name = "a" * 255  # Excel sheet names have limits
        config = {
            'activities': {
                long_name: {
                    'priority': 'medium',
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
        report_gen = ReportGenerator(optimizer)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            # Should handle long names gracefully
            report_gen.export_schedules_to_excel(temp_path)
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_excel_with_special_characters(self):
        """Test Excel export with special characters in names."""
        config = {
            'activities': {
                'activity/with\\special:chars*?': {
                    'priority': 'medium',
                    'effort_per_cycle': 1.0,
                    'frequency': 1,
                    'theme': 'theme<>|chars',
                    'original_start_month': 6
                }
            },
            'resource_availability': {
                'theme<>|chars': [2.0] * 12
            }
        }
        
        optimizer = EnhancedBAUOptimizer(config)
        report_gen = ReportGenerator(optimizer)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            # Should handle special characters
            report_gen.export_schedules_to_excel(temp_path)
            assert os.path.exists(temp_path)
        except (ValueError, OSError):
            # Some special characters might not be allowed
            pass
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_report_with_optimizer_having_no_activities(self):
        """Test report generation with optimizer that has no activities."""
        empty_config = {
            'activities': {},
            'resource_availability': {'unused_theme': [1.0] * 12}
        }
        
        empty_optimizer = EnhancedBAUOptimizer(empty_config)
        report_gen = ReportGenerator(empty_optimizer)
        report = report_gen.generate_summary_report()
        
        assert report['total_activities'] == 0
        assert report['changes_made'] == 0
        assert len(report['changes_detail']) == 0
        assert report['current_gaps_total'] >= 0
        assert report['optimized_gaps_total'] >= 0
    
    def test_report_with_optimizer_having_no_resources(self):
        """Test report generation with optimizer that has no resource themes."""
        config_no_resources = {
            'activities': {
                'orphan': {
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
            no_resource_optimizer = EnhancedBAUOptimizer(config_no_resources)
            report_gen = ReportGenerator(no_resource_optimizer)
            report = report_gen.generate_summary_report()
            
            assert report['total_activities'] == 1
            assert len(report['resource_themes']) == 0
        except (KeyError, IndexError):
            # Acceptable to fail with no matching resource themes
            pass
    
    def test_concurrent_report_generation(self):
        """Test that multiple report generators can work simultaneously."""
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
        
        report_gen1 = ReportGenerator(optimizer1)
        report_gen2 = ReportGenerator(optimizer2)
        
        # Should be able to generate reports independently
        report1 = report_gen1.generate_summary_report()
        report2 = report_gen2.generate_summary_report()
        
        assert report1['total_activities'] != report2['total_activities']
        assert report1['resource_themes'] != report2['resource_themes']