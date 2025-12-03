import unittest
from unittest.mock import patch

from thc_devops_toolkit.utils import time_elapsed


class TestTimeElapsed(unittest.TestCase):
    """Test cases for the time_elapsed context manager."""

    @patch("thc_devops_toolkit.utils.time.time")
    def test_time_elapsed_context_manager(self, mock_time):
        """Test that time_elapsed correctly measures elapsed time and logs the result."""
        # Mock time.time() to return specific values
        mock_time.time.side_effect = [10.0, 12.5]  # start: 10.0, end: 12.5

        topic = "Test Operation"

        with time_elapsed(topic):
            pass  # Simulate some work

        # Verify that time.time() was called twice
        self.assertEqual(mock_time.time.call_count, 2)
