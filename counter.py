import RPi.GPIO as GPIO
from threading import Timer
import time
import atexit
from collections import OrderedDict
import collections

# IN  | OUT | Color
# 15  | 22  | Blue 
# 16  | 23  | Green
# 18  | 24  | Red

class Rin:
    pins = {}

    @classmethod
    def init(cls, mode=GPIO.BOARD):
        GPIO.setmode(mode)

    @classmethod
    def pin(cls, number):
        if number not in cls.pins:
            cls.pins[number] = cls(number)

    def __init__(self, number, in_or_out):
        self.falling = None
        self.rising = None

        self.number = number
        self.in_or_out = in_or_out
        self.bounce_time = 0 # ms

        GPIO.setup(number, in_or_out)

        self.event_time = time.time() * 1000
        self.state = GPIO.input(self.number)

        self.previous_time = self.event_time
        self.previous_state = self.state

        GPIO.add_event_detect(self.number, GPIO.BOTH, callback = self.Edge)
      
    def Edge(self, channel):
        if self.state == self.previous_state:
            return # Ignore series of events with same state. Am I sure about this? Not really.

        if self.previous_time and (self.event_time - self.previous_time < self.bounce_time):
            return # Debouncing in action

        self.previous_time = self.event_time
        self.previous_state = self.state

        self.event_time = time.time() * 1000
        self.state = GPIO.input(self.number)

        state_duration = (self.event_time - self.previous_time if self.previous_time else 0)

        if self.state:
            if self.rising: self.rising(self.number)
        else:
            if self.falling: self.falling(self.number)

        if self.changed: self.changed(self.number, self.state)

Rin.init()
