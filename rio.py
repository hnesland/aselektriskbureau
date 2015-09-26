# Object Oriented GPIO manipulation for Raspberry Pi

import RPi.GPIO as GPIO
from threading import Timer
import time


class Rio:
    pins = {}

    @staticmethod
    def init(mode=GPIO.BOARD):
        GPIO.setmode(mode)

    @staticmethod
    def cleanup():
        GPIO.cleanup()

    @classmethod
    def get(cls, number):
        if number not in cls.pins:
            cls.pins[number] = cls(number)
        return cls.pins[number]

    def __init__(self):
        pass


class Rin(Rio):
    def __init__(self, number):
        self.falling = None
        self.rising = None
        self.changed = None

        self.number = number
        self.bounce_interval = 0  # ms

        GPIO.setup(number, GPIO.IN)
        GPIO.add_event_detect(self.number, GPIO.BOTH, callback=self.edge)

        self.event_time = self.__ms_time()
        self.current_state = GPIO.input(self.number)

        self.previous_time = self.event_time
        self.previous_state = self.current_state

        self.bounce_time = self.event_time
        self.bounce_timer = None

    @property
    def state(self):
        return GPIO.input(self.number)

    @property
    def text_state(self):
        return "HIGH" if self.state else "LOW"

    def edge(self, channel):
        self.event(self.__ms_time(), self.state)

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
                self.rising(current_time, state_duration)
        else:
            if self.falling:
                self.falling(current_time, state_duration)

        if self.changed:
            self.changed(self.current_state, current_time, state_duration)

    def __ms_time(self):
        return round(time.time() * 1000)


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


class RioTest:
    """
        This class performs physical tests for the Rin and Rout classes. This needs to be run on the actual RPi,
        and requires connecting out to in via current limiting resistor, according to the circuit drawn bellow.

        IN[13]    OUT[11]
        o         o
        |   ___   |
        \--|___|--o----\
           1kOhm  |    |
                 .-.  ___
           10kOhm| |  \ /  LED Diode (with ~270 Ohm resistor) [optional]
                 '-'  ---
                  |    |
                  o----/
                  |
                  o GND[9]

        This way, when OUT is pulled HIGH the input should also register HIGH state, and if the output is not powered
        the input should also be in LOW state.

        The 1kOhm resistor is meant to protect the chip in case pins are setup incorrectly and 10k Ohm resistor is meant
         to limit current flowing through the circuit ( Lookup Pull-Down/Pull-Up conecept here:
         http://elinux.org/RPi_Tutorial_EGHS:Switch_Input ).

        You can optionally add a diode with resistor in series to limit current, which resistor exactly you need you can
         learn here: http://www.instructables.com/id/Choosing-The-Resistor-To-Use-With-LEDs/?ALLSTEPS
    """

    def __init__(self, **pins):
        """
            :param pin: Pin number for input (numbered by board number or BCM depending on value passed to init()
            :param pout: Pin number for output (numbered by board number or BCM depending on value passed to init()
        """

        self.pin = pins['pin']
        self.pout = pins['pout']

        self.rin = Rin.get(self.pin)
        self.rout = Rout.get(self.pout)

        self.rising_called = None
        self.falling_called = None
        self.changed_called = None

    @staticmethod
    def result(expected, actual):
        ok = '\033[92m'
        fail = '\033[91m'
        end = '\033[0m'

        if expected == actual:
            print ok + actual + end
        else:
            print fail + actual + end

    def test_regular(self):
        rin  = Rin.get(self.pin)
        rout = Rout.get(self.pout)

        print 'HIGH for 1 second (check if led is on).'
        rout.high()
        time.sleep(1)

        print 'HIGH (10ms delay) ...',
        rout.high()
        time.sleep(0.01)
        self.result("HIGH", rin.text_state)

        print 'LOW  (10ms delay)...',
        rout.low()
        time.sleep(0.01)
        self.result("LOW", rin.text_state)

        print 'HIGH (1ms delay) ...',
        rout.high()
        time.sleep(0.001)
        self.result("HIGH", rin.text_state)

        print 'LOW  (1ms delay)...',
        rout.low()
        time.sleep(0.001)
        self.result("LOW", rin.text_state)

        print 'HIGH (no delay)...',
        rout.high()
        self.result("HIGH", rin.text_state)

        print 'LOW  (no delay)...',
        rout.low()
        self.result("LOW", rin.text_state)

    def high(self, sleep_ms=0):
        self.rout.high()
        if sleep_ms:
            time.sleep(sleep_ms / 1000)

    def low(self, sleep_ms=0):
        self.rout.high()
        if sleep_ms:
            time.sleep(sleep_ms / 1000)

    def test_callbacks(self):
        print '\nSetting up callback tests'

        self.rin.changed = self.changed
        self.rin.rising = self.rising
        self.rin.falling = self.falling

        print "\nRaise 10ms delay."
        self.high(10)

        print "\nFall  10ms delay."
        self.low(0.1)

        print "\nRaise, Fall, Raise (5ms delay)"
        self.high(5)
        self.low(5)
        self.high(5)

        print '\nQuick fall, raise and fall again'
        self.low(5)
        self.high(5)
        self.low(5)

    def rising(self, current_time, state_duration):
        self.rising_called = {'current_time': current_time, 'state_duration': state_duration}
        print 'Rising called', self.rising_called

    def falling(self, current_time, state_duration):
        self.falling_called = {'current_time': current_time, 'state_duration': state_duration}
        print 'Falling called', self.falling_called

    def changed(self, current_state, current_time, state_duration):
        self.changed_called = {'current_state': current_state, 'current_time': current_time, 'state_duration': state_duration}
        print 'Changed called', self.changed_called


if __name__ == "__main__":
    Rio.init()
    tester = RioTest(pin=13, pout=11)
    tester.test_regular()
    tester.test_callbacks()

    print 'Waiting one second for all tests to finish and timer to stop'
    time.sleep(1)

    Rio.cleanup()