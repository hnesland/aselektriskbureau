"""
# Rotary Dial Parser
# Expects the following hardware rules:
# 1 is 1 pulse
# 9 is 9 pulses
# 0 is 10 pulses
"""


from threading import Timer
from RPi import GPIO


class HardwareAbstractionLayer(object):
    """
    Superclass to allow disambiguation between different implementations of
    dialer hardware from different phone conversion projects.
    """

    pulse_count = 0  # Count the number of pulses detected

    onhook_timer = None  # Timer object to ensure we're on hook
    debounce_timer = None  # Timer object for debounce cleaning.

    dialling = False
    hook = False

    pins = {
        "earpiece": None,
        "digits": None,
        "dialling": None
    }

    callback_digit = None
    callback_onhook = None
    callback_offhook = None

    pulse_table = {
        1:1,
        2:2,
        3:3,
        4:4,
        5:5,
        6:6,
        7:7,
        8:8,
        9:9,
        10:0
    }

    def __init__(self):
        GPIO.setmode(GPIO.BCM)  # Broadcom pin numbers.

        GPIO.setup(self.pins["dialling"], GPIO.IN) #Listen for dialling start/end.
        GPIO.add_event_detect(self.pins["dialling"],
                              GPIO.BOTH,
                              callback=self.dialling_state)

        GPIO.setup(self.pins["digits"], GPIO.IN) #Listen for digits.
        GPIO.add_event_detect(self.pins["digits"],
                              GPIO.BOTH,
                              callback=self.detect_clicks)

        # Listen for on/off hooks
        GPIO.setup(self.pins["earpiece"], GPIO.IN)
        GPIO.add_event_detect(self.pins["earpiece"],
                              GPIO.BOTH,
                              callback=self.earpiece_event,
                              bouncetime=100)  # Is bouncetime a debounce constant!?

    def clean_exit(self):
        """
        Safely close the GPIO when closing the app.
        """
        GPIO.cleanup()

    def dialling_state(self, channel):
        """
        GPIO detects whether the rotary dial is active.
        """
        if not GPIO.input(channel):
            return None

        if not self.dialling:
            self.dialling = True
        else:
            pulses = self.pulse_count
            if pulses % 2:
                raise IOError("Count is not divisible by 2")
            self.callback_digit(self.pulse_table[pulses])

    def detect_clicks(self, channel):
        """
        GPIO detects a state change on the rotary detection pin. This is where
        I count the clicks and assemble a digit from the data.
        """
        if GPIO.input(channel):
            self.pulse_count += 1

    def earpiece_event(self, channel):
        """
        GPIO detects a state change
        """
        self.hook = bool(GPIO.input(channel))
        if self.hook:
            self.callback_onhook()
        else:
            self.callback_offhook()

    def register_callbacks(self,
                           callback_digit,
                           callback_onhook,
                           callback_offhook):
        """
        Register callbacks for the interface with the calling application
        """
        self.callback_digit = callback_digit
        self.callback_onhook = callback_onhook
        self.callback_offhook = callback_offhook


class AstralHAL(HardwareAbstractionLayer):
    """
    Subclass of HardwareAbstractionLayer to support the dialer in phones from
    the late period of Astral PLC.
    """
    def __init__(self):
        self.pins = {
            "earpiece": 22,
            "digits" : 17,
            "dialling": 27
        }
        super(AstralHAL, self).__init__()


class ElektriskHAL(HardwareAbstractionLayer):
    """
    Subclass of HardwareAbstractionLayer to support the dialer in the
    AS Elektrisk Bureau desk phone.
    """

    def __init__(self):
        self.pins = {
            "earpiece": 3,
            "digits": 4,
            "dialling": None
        }
        super(ElektriskHAL, self).__init__()


