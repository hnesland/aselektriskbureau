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
    def __init__(self, number):
        self.falling = None
        self.rising = None
        self.changed = None

        self.number = number
        self.bounce_interval = 0  # ms

        self.event_time = time.time() * 1000
        self.current_state = GPIO.input(self.number)

        self.previous_time = self.event_time
        self.previous_state = self.current_state

        self.bounce_time = self.event_time
        self.bounce_timer = None

        GPIO.setup(number, GPIO.IN)
        GPIO.add_event_detect(self.number, GPIO.BOTH, callback=self.edge)

    def state(self):
        GPIO.input(self.number)

    def text_state(self):
        "HIGH" if self.state() else "LOW"

    def edge(self, channel):
        self.event(time.time() * 1000, self.state())

    def event(self, current_time, current_state):
        """
        Processes event.

        What we really want is to debounce raising/falling events and gather length of the previous
        state (eg. how long button was pressed). The problem seems to be how do we handle debouncing?
        Ideally a very short connection/disconnection series should be for example: 10101111| (Rising)
        so the first and last state are the same and next we can expect 01010000| (Falling)
        [where | is a cutoff for debouncing].
        But what if we get something like this: 1010111110|00000000
        Obviously we want to do a Rising event, but do we also raise a Falling event?
        If we don't then that would mean one Raising event gets followed by another Rising event which we don't
        necessarily expect. Ideally we'd like to get alternating stream of events.
        Keep it mind however that this is not a guarantee. It's possible to receive several HIGH signals in a anyway.
        """
        if current_time - self.bounce_time < self.bounce_interval:
            self.bounce_time = current_time

            # We block the event if it happened to fast after previous one. But if it last longer then bounce timer
            # we trigger it. We pass the original time of event triggering.
            if self.bounce_timer:
                self.bounce_timer.cancel()
            self.bounce_timer = Timer(self.bounce_interval, self.event, current_time, current_state)
            self.bounce_timer.start()

            return

        self.previous_time = self.event_time
        self.previous_state = self.current_state

        self.event_time = current_time
        self.current_state = current_state

        state_duration = self.event_time - self.previous_time

        if self.current_state == GPIO.HIGH:
            if self.rising:
                self.rising(self.number, current_time, state_duration)
        else:
            if self.falling:
                self.falling(self.number, current_time, state_duration)

        if self.changed:
            self.changed(self.number, self.current_state, current_time, state_duration)


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


if __name__ == "__main__":
    def test(pin, pout):
        """
        This method performs physical tests for the Rin and Rout classes. This needs to be run on the actual RPi,
        and requires connecting out to in via current limiting resistor, according to the circuit drawn bellow.

         o OUT
         |
        ___
        \ / - LED Diode (optional)
        ---
         |   ___
         o--|___|---o IN
         |  1kOhm
        .-.
        | |
        | | 10k Ohm
        '-'
         |
         o GND

        This way, when OUT is pulled HIGH the input should also register HIGH state, and if the output is not powered
        the input should also be in LOW state.

        The 1kOhm resistor is meant to protect the chip in case pins are setup incorrectly and 10k Ohm resistor is meant
         to limit current flowing through the circuit ( Lookup Pull-Down/Pull-Up conecept here:
         http://elinux.org/RPi_Tutorial_EGHS:Switch_Input ).

        :param pin: Pin number for input (numbered by board number or BCM depending on value passed to init()
        :param pout: Pin number for output (numbered by board number or BCM depending on value passed to init()
        :return:
        """

        rin = Rin(pin)
        rout = Rout(pout)

        print 'HIGH for 3 seconds (check if led is on).'
        rout.high()
        time.sleep(3)

        print('High for 0.1s (with 10ms delay) ...'),
        rout.high()
        time.sleep(0.01)
        print rin.text_state()

        print('Low for 0.1s (with 10ms delay)...'),
        rout.low()
        time.sleep(0.01)
        print rin.text_state()

        print('High for 0.1s (with 1ms delay) ...'),
        rout.high()
        time.sleep(0.001)
        print rin.text_state()

        print('Low for 0.1s (with 1ms delay)...'),
        rout.low()
        time.sleep(0.001)
        print rin.text_state()

        print('High for 0.1s ...'),
        rout.high()
        print rin.text_state()

        print('Low for 0.1s ...'),
        rout.low()
        print rin.text_state()

        pass


    test()
