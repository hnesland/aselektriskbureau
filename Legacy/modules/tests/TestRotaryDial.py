"""
Unit tests for module Rotary Dial. This could be tricky to implement due to
the need for hardware interaction to achieve tests.

User should add the github root directory to their python site-package.
"""

import unittest
from phonedaemon.modules.RotaryDial import RotaryDial


class TestSampleTest(unittest.TestCase):
    """
    Includes all tests for the DialTimer class.
    """
    def setUp(self):
        """
        Defines variables for the test cases.
        """
        self.sample_flag = False

    def callback(self):
        """
        Needed to verify callback cases.
        """

        self.sample_flag = True

    def test_onhook(self):
        """
        Test the basic case: This is currently just a prototype.
        """
        self.assertFalse(self.sample_flag)
        self.callback()
        self.assertTrue(self.sample_flag)

if __name__ == '__main__':
    unittest.main()
