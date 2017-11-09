# Object Oriented GPIO manipulation for Raspberry Pi

from threading import Timer, Lock, RLock
import time
import functools

import RPi.GPIO as GPIO


def synchronized(wrapped):
    """ Synchronization decorator. """

    meta_lock = Lock()

    @functools.wraps(wrapped)
    def _wrapper(self, *args, **kwargs):
        with meta_lock:
            lock = vars(self).setdefault("__lock_"+wrapped.__name__, RLock())

        with lock:
            return wrapped(self, *args, **kwargs)

    return _wrapper


class Rio:
    pins = {}
    lock = Lock()

    @staticmethod
    def init(mode=GPIO.BOARD):
        GPIO.setmode(mode)

    @classmethod
    def cleanup(cls):
        for number, rin in cls.pins.iteritems():
            rin.destroy()

        cls.pins = {}
        GPIO.cleanup()

    @classmethod
    def get(cls, number):
        try:
            cls.lock.acquire()
            if number not in cls.pins:
                cls.pins[number] = cls(number)
        finally:
            cls.lock.release()

        return cls.pins[number]

    def __init__(self):
        pass


class Rin(Rio):
    def __init__(self, number, bounce_interval=0):
        self.falling = None
        self.rising = None
        self.changed = None

        self.number = number
        self.bounce_interval = bounce_interval  # ms

        GPIO.setup(number, GPIO.IN)
        GPIO.add_event_detect(self.number, GPIO.BOTH, callback=self.edge)

        self.event_time = self.ms_time()
        self.current_state = self.state()

        self.previous_time = self.event_time
        self.previous_state = self.current_state

        self.bounce_time = 0
        self.bounce_timer = None

    def reset(self):
        self.event_time = self.ms_time()
        self.current_state = self.state()

        self.previous_time = self.event_time
        self.previous_state = self.current_state

        self.bounce_time = 0
        self.bounce_timer = None

    def edge(self, channel):
        self.debounce(self.ms_time(), self.state())

    @synchronized
    def debounce(self, change_time, new_state):
        """
        Decide if event (rise/fall) should be debounced.

        What we really want is to debounce raising/falling events and gather length of the previous
        state (eg. how long button was pressed).

        Sequence of changes (ever 5ms) -> Expected events. (1 - Raise, F - Fall, _ - No change)
        10101__ -> Raise at 0 ms
        101_0__ -> Raise at 0 ms, Fall at 20ms
        1010___ -> Raise at 0 ms, Fall at 15ms
        All should get debounced.

        Tricky part is there's not real guarantee that there cannot be two falling events in a row. This is a dump from
        a real test:

        -----------------------------------------------------------------------------------------------
        LP |          Trigger |  Time [ms] | Length[ms] | Count | State
         0 |      Pulse - LOW |      0[ms] |      0[ms] |     - | -
         0 |  Rotation - HIGH |      0[ms] |      0[ms] |     - | -
         1 |  Rotation - HIGH |      0[ms] |  10958[ms] |     - | -
         2 |   Rotation - LOW |     74[ms] |     74[ms] |     - | -
         3 |   Rotation - LOW |     76[ms] |      2[ms] |     - | -
         4 |   Rotation - LOW |     82[ms] |      6[ms] |     - | -
         5 |  Rotation - HIGH |    118[ms] |     36[ms] |     - | -
         6 |   Rotation - LOW |    185[ms] |     67[ms] |     - | -
         7 |   Rotation - LOW |    186[ms] |      1[ms] |     - | -
         8 |   Rotation - LOW |    198[ms] |     12[ms] |     - | -
         9 |  Rotation - HIGH |    228[ms] |     30[ms] |     - | -
        10 |  Rotation - HIGH |    229[ms] |      1[ms] |     - | -
        11 |   Rotation - LOW |    294[ms] |     65[ms] |     - | -
        12 |   Rotation - LOW |    296[ms] |      2[ms] |     - | -

        Additionally even with debuncing turned on, sometimes duplicate events will come through with length < debounce
        time. There must be several bugs related to concurrency in that library. For that reason we write our own
        debouncing.
        """

        if self.bounce_interval == 0:
            self.event(change_time, new_state)
            return False

        if not self.bounce_timer:
            if new_state != self.current_state:
                self.bounce_timer = Timer(self.bounce_interval / 1000.0, self.event, [change_time, new_state])
                self.bounce_timer.start()
        else:
            if new_state == self.current_state:
                self.bounce_timer.cancel()
                self.bounce_timer = None

    @synchronized
    def event(self, change_time, new_state):
        """
        Processes event, including debouncing and measurement of previous state length.
        """

        self.bounce_timer = None

        self.previous_time = self.event_time
        self.previous_state = self.current_state

        self.event_time = change_time
        self.current_state = new_state

        state_duration = self.event_time - self.previous_time

        if self.current_state == GPIO.HIGH:
            if self.rising:
                self.rising(change_time, state_duration)
        else:
            if self.falling:
                self.falling(change_time, state_duration)

        if self.changed:
            self.changed(new_state, change_time, state_duration)

    def state(self):
        return GPIO.input(self.number)

    @property
    def text_state(self):
        return "HIGH" if self.state() else "LOW"

    def ms_time(self):
        return round(time.time() * 1000)

    def destroy(self):
        GPIO.remove_event_detect(self.number)


class Rout(Rio):
    def __init__(self, number):
        self.number = number
        self.state = GPIO.LOW
        GPIO.setup(number, GPIO.OUT)

    def set(self, new_state):
        self.state = new_state
        GPIO.output(self.number, self.state)

    def high(self, timeout=None):
        self.state = GPIO.HIGH
        GPIO.output(self.number, self.state)
        if timeout:
            Timer(timeout, self.low).start()

    on = high

    def low(self, timeout=None):
        self.state = GPIO.LOW
        GPIO.output(self.number, self.state)
        if timeout:
            Timer(timeout, self.high).start()

    off = low

    def flip(self, timeout=None):
        self.state = not self.state
        GPIO.output(self.number, self.state)
        if timeout:
            Timer(timeout, self.flip).start()

    def destroy(self):
        pass
