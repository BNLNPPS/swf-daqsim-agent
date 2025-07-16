import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path to import daq module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daq.daq import DAQ, Monitor


class TestDAQ:
    """Test cases for DAQ class functionality"""

    def test_metadata_generation(self):
        """Test that metadata is generated correctly"""
        # Create a DAQ instance with minimal configuration
        daq = DAQ(
            schedule_f='config/schedule-rt.yml',
            destination='',
            verbose=False
        )
        
        # Test metadata generation
        filename = "test_file.stf"
        start_time = datetime(2025, 1, 15, 10, 30, 0)
        end_time = datetime(2025, 1, 15, 10, 30, 5)
        
        # Set state and substate for testing
        daq.state = "RUNNING"
        daq.substate = "PHYSICS"
        
        metadata = daq.metadata(filename, start_time, end_time)
        
        # Verify metadata structure and content
        assert metadata['filename'] == filename
        assert metadata['start'] == "20250115103000"
        assert metadata['end'] == "20250115103005"
        assert metadata['state'] == "RUNNING"
        assert metadata['substate'] == "PHYSICS"
        
        # Verify all expected keys are present
        expected_keys = ['filename', 'start', 'end', 'state', 'substate']
        assert all(key in metadata for key in expected_keys)

    def test_get_time_method(self):
        """Test that get_time method returns formatted time"""
        daq = DAQ(
            schedule_f='config/schedule-rt.yml',
            destination='',
            verbose=False
        )
        
        # This test requires a SimPy environment to be set up
        # We'll test it by calling start_run and then testing get_time
        daq.start_run()
        
        # Test that get_time returns a string with 's' suffix
        time_str = daq.get_time()
        assert isinstance(time_str, str)
        assert time_str.endswith('s')
        assert '.' in time_str  # Should contain decimal point for formatting


class TestMonitor:
    """Test cases for Monitor class functionality"""

    def test_monitor_initialization(self):
        """Test Monitor class initialization"""
        size = 100
        monitor = Monitor(size=size)
        
        # Verify buffer is initialized correctly
        assert monitor.buffer.shape == (size,)
        assert monitor.buffer.dtype.name == 'float64'
        
        # Verify buffer is initialized with zeros
        assert (monitor.buffer == 0.0).all()

    def test_monitor_default_initialization(self):
        """Test Monitor class with default size"""
        monitor = Monitor()
        
        # Verify default size is 0
        assert monitor.buffer.shape == (0,)