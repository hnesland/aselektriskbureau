"""
# Rotary Dial Parser
# Expects the following hardware rules:
# 1 is 1 pulse
# 9 is 9 pulses
# 0 is 10 pulses
"""

import time
from threading import Timer
import RPi.GPIO as GPIO

class HardwareAbstractionLayer(object):
    """
    Superclass to allow disambiguation between different implementations of
    dialer hardware from different phone conversion projects.
    """

    # TODO: Why are these pins hardcoded? Should be config. So should Pi/not.
    # We'll be reading BCM GPIO 4 (pin 7 on board)
    pin_rotary = 4

    # We'll be reading on/off hook events from BCM GPIO 3
    pin_onhook = 3

    # After 900ms, we assume the rotation is done and we get
    # the final digit.
    digit_timeout = 0.9

    # We keep a counter to count each pulse.
    current_digit = 0

    # Simple timer for handling the number callback
    number_timeout = None

    last_input = 0

    # Timer to ensure we're on hook
    onhook_timer = None
    should_verify_hook = True
    
    def __init__(self):
        # Set GPIO mode to Broadcom SOC numbering
        GPIO.setmode(GPIO.BCM)

        # Listen for rotary movements
        GPIO.setup(self.pin_rotary, GPIO.IN)
        GPIO.add_event_detect(self.pin_rotary,
                              GPIO.BOTH,
                              callback=self.click_counter)

        # Listen for on/off hooks
        GPIO.setup(self.pin_onhook, GPIO.IN)
        GPIO.add_event_detect(self.pin_onhook,
                              GPIO.BOTH,
                              callback=self.earpiece_event,
                              bouncetime=100)

        self.onhook_timer = Timer(2, self.verifyHook)
        self.onhook_timer.start()

    def click_counter(self, channel):
        """
        Increment counter when click heard, and create digit count timeout.
        """
        click_input = GPIO.input(self.pin_rotary)
        #print "[INPUT] %s (%s)" % (click_input, channel)
        if click_input and not self.last_input:
            self.current_digit += 1

            if self.number_timeout is not None:
                self.number_timeout.cancel()

            self.number_timeout = Timer(self.digit_timeout,
                                        self.number_detected)
            self.number_timeout.start()
        self.last_input = click_input
   #     time.sleep(0.002)

    def earpiece_event(self, channel):
        """
        Wrapper to separate on/off hook events.
        """
        hook_input = GPIO.input(self.pin_onhook)
        if hook_input:
            self.hook_state = 1
            self.OffHookCallback()
        else:
            self.hook_state = 0
            self.OnHookCallback()

    def number_detected(self):
        """
        If a number has been detected, callback to calling application
        """
        if self.current_digit == 10:
            self.current_digit = 0
        self.NumberCallback(self.current_digit)
        self.current_digit = 0

    def register_callback(self,
                          NumberCallback,
                          OffHookCallback,
                          OnHookCallback,
                          OnVerifyHook):
        """
        Register callbacks for the interface with the calling application
        """
        self.NumberCallback = NumberCallback
        self.OffHookCallback = OffHookCallback
        self.OnHookCallback = OnHookCallback
        self.OnVerifyHook = OnVerifyHook

        hook_input = GPIO.input(self.pin_onhook)
        if hook_input:
            self.OffHookCallback()
        else:
            self.OnHookCallback()

    def StopVerifyHook(self):
        """
        Set state to stop verifying hook.
        """
        self.should_verify_hook = False

    def verifyHook(self):
        """
        Verify whether the hook is on.
        """
        while self.should_verify_hook:
            state = GPIO.input(self.pin_onhook)
            self.OnVerifyHook(state)
            time.sleep(1)


class AstralHAL(HardwareAbstractionLayer):
    """
    Subclass of HardwareAbstractionLayer to support the dialer in phones from
    the late period of Astral PLC.
    """
    def __init__(self):
        super(AstralHAL, self).__init__()

    def something_astral_specific(self):
        """
        Do something specific to the Astral wall phone.
        """
        print 'Doing something!'

class ElektriskHAL(HardwareAbstractionLayer):
    """
    Subclass of HardwareAbstractionLayer to support the dialer in the
    AS Elektrisk Bureau desk phone.
    """

    def __init__(self):
        super(ElektriskHAL, self).__init__()

    def something_aseb_specific(self):
        """
        Do something specific to the AS Elektrisk Bureau desk phone.
        """
        print 'Doing something!'


