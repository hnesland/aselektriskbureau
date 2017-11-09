"""
Unit tests for module DialTimer.

User should add the github root directory to their python site-package.
"""

import unittest
import time
from phonedaemon.modules.DialTimer import DialTimer


class TestNormalTimer(unittest.TestCase):
    """
    Tests case where timer has been created with default timeout.
    """
    def setUp(self):
        """
        Defines variables for the test cases.
        """
        self.default_flag = False
        self.reset_flag = False
        self.default_timer = DialTimer()
        self.reset_timer = DialTimer()
        self.default_timer.register_callback(self.default_callback)
        self.reset_timer.register_callback(self.reset_callback)

    def default_callback(self):
        """
        Sets a flag to True when the timer expires.
        """
        self.default_flag = True

    def reset_callback(self):
        """
        Sets a flag to True when the timer expires.
        """
        self.reset_flag = True

    def test_default(self):
        """
        Test the basic case: Start a timer and wait for it to expire.
        """
        self.default_timer.start()
        time.sleep(2)
        self.assertFalse(self.default_flag)
        time.sleep(2)
        self.assertTrue(self.default_flag)

    def test_reset(self):
        """
        Test the common case: Start a timer, reset and wait for it to expire.
        """
        self.reset_timer.start()
        time.sleep(2)
        self.assertFalse(self.reset_flag)
        self.reset_timer.reset()
        self.assertFalse(self.reset_flag)
        time.sleep(2)
        self.assertFalse(self.reset_flag)
        time.sleep(2)
        self.assertTrue(self.reset_flag)


class TestLongTimer(unittest.TestCase):
    """
    Tests case where timer has been created with long timeout.
    """
    def setUp(self):
        """
        Defines variables for the test cases.
        """
        self.default_flag = False
        self.default_timer = DialTimer(timeout_length=8)
        self.default_timer.register_callback(self.default_callback)

    def default_callback(self):
        """
        Sets a flag to True when the timer expires.
        """
        self.default_flag = True

    def test_default(self):
        """
        Test the basic case: Start a timer and wait for it to expire.
        """
        self.default_timer.start()
        time.sleep(6)
        self.assertFalse(self.default_flag)
        time.sleep(2)
        self.assertTrue(self.default_flag)


if __name__ == '__main__':
    unittest.main()
