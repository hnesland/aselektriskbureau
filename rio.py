# Object Oriented GPIO manipulation for Raspberry Pi

import RPi.GPIO as GPIO
from threading import Timer
import time


class Rio:
    pins = {}

    @staticmethod
    def init(cls, mode=GPIO.BOARD):
        GPIO.setmode(mode)



    @classmethod
    def pin(cls, number):
        if number not in cls.pins:
            cls.pins[number] = cls(number)

    def __init__(self):
        pass


class Rin(Rio):
    skip_repeats = False

    def __init__(self, number):
        self.falling = None
        self.rising = None
        self.changed = None

        self.number = number
        self.bounce_time = 0 # ms

        self.event_time = time.time() * 1000
        self.state = GPIO.input(self.number)

        self.previous_time = self.event_time
        self.previous_state = self.state

        GPIO.setup(number, GPIO.IN)
        GPIO.add_event_detect(self.number, GPIO.BOTH, callback = self.Edge)
      
    def Edge(self, channel):
        if self.event_time - self.previous_time < self.bounce_time:
            return # Debouncing in action

        if self.skip_repeats and self.state == self.previous_state:
            return # Ignore series of events with same state.

        self.previous_time = self.event_time
        self.previous_state = self.state

        self.event_time = time.time() * 1000
        self.state = GPIO.input(self.number)

        state_duration = self.event_time - self.previous_time

        if self.state:
            if self.rising: self.rising(self.number, state_duration)
        else:
            if self.falling: self.falling(self.number, state_duration)

        if self.changed: self.changed(self.number, self.state, state_duration)


class Rout(Rio):
    def __init__(self, number):
        self.number = number
        self.state = GPIO.LOW
        GPIO.setup(number, GPIO.OUT)

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
