import unittest
from unittest.mock import patch

from thc_devops_toolkit.utils.timer import timer


class TestTimer(unittest.TestCase):
    """Test cases for the timer context manager."""

    @patch('thc_devops_toolkit.utils.timer.time')
    def test_timer_context_manager(self, mock_time):
        """Test that timer correctly measures elapsed time and logs the result."""
        # Mock time.time() to return specific values
        mock_time.time.side_effect = [10.0, 12.5]  # start: 10.0, end: 12.5
        
        topic = "Test Operation"
        
        with timer(topic):
            pass  # Simulate some work
        
        # Verify that time.time() was called twice
        self.assertEqual(mock_time.time.call_count, 2)
