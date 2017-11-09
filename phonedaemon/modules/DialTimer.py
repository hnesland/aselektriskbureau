"""
This module simply provides the class DialTimer, which abstracts
threading.Timer to provide a more appropriate interface to DialTimer()
"""


from threading import Timer


class DialTimer(object):
    """
    This class runs a timer in the background. When the timer expires without
    Reset() being called, the number is sent to the SIP handler for dialling.
    This abstraction is probably very unnecessary, but it keeps
    TelephoneDaemon() a little cleaner.

    NOTE: It may be that I can rewrite this as a subclass of Timer.
    Investigate!
    """

    timeout_length = 3  # Seems a sensible default to use.
    timer_object = None
    timeout_callback = None

    def __init__(self, timeout_length=None):
        """
        Set up the class.
        """

        if timeout_length:
            self.timeout_length = timeout_length

    def create(self):
        """
        Creates a Timer() with the specified values.
        """
        self.timer_object = Timer(self.timeout_length, self.timeout_callback)

    def start(self):
        """
        Starts a new timer.
        """
        self.create()
        self.timer_object.start()

    def reset(self):
        """
        Reset the timer.
        """
        self.timer_object.cancel()
        self.create()
        self.timer_object.start()

    # Handles the callbacks we're supplying
    def register_callback(self, callback):
        """
        Register callback for timer. This is probably also super-unnecessary.
        """
        self.timeout_callback = callback
