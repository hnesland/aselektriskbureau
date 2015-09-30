# Object Oriented GPIO manipulation for Raspberry Pi

import RPi.GPIO as GPIO
from threading import Timer, Lock
import time


class Rio:
    pins = {}
    lock = Lock()

    @staticmethod
    def init(mode=GPIO.BOARD):
        GPIO.setmode(mode)

    @staticmethod
    def cleanup():
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
        \--|___|--o
          10kOhm  |
                 .-.
           270Ohm| |
                 '-'
                  |
                 ___
                 \ /  LED Diode (with ~270 Ohm resistor)  is optional
                 ---
                  |
                  o GND[9]

        This way, when OUT is pulled HIGH the input should also register HIGH state, and if the output is not powered
        the input should also be in LOW state.

        The 10kOhm resistor is meant to protect the chip in case pins are setup incorrectly and limit current flowing
        through the circuit. Diode with current limiting resistor can be added to have visual indicator of pin state
        and correctness of the connection, although it'll only light up for a second at the start of the test.

        You can optionally add a diode with resistor in series to limit current, which resistor exactly you need you can
         learn here: http://www.instructables.com/id/Choosing-The-Resistor-To-Use-With-LEDs/?ALLSTEPS
    """

    minimal_change_duration = 5  # ms.

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

        self.call_stack = []

    @staticmethod
    def result(expected, actual):
        ok = '\033[92m'
        fail = '\033[91m'
        exp = '\033[93m'
        end = '\033[0m'

        if expected == actual:
            print ok, actual, end
        else:
            print fail, actual, end, "Expected", exp, expected, end

    def test_regular(self):
        rin = Rin.get(self.pin)
        rout = Rout.get(self.pout)

        print 'HIGH for 1 second (check if led is on).'
        rout.high()
        time.sleep(1)

        print 'HIGH (10ms delay) ...',
        rout.high()
        time.sleep(0.01)
        self.result("HIGH", rin.text_state)

        print 'LOW  (10ms delay) ...',
        rout.low()
        time.sleep(0.01)
        self.result("LOW", rin.text_state)

        print 'HIGH (1ms delay) ....',
        rout.high()
        time.sleep(0.001)
        self.result("HIGH", rin.text_state)

        print 'LOW  (1ms delay) ....',
        rout.low()
        time.sleep(0.001)
        self.result("LOW", rin.text_state)

        print 'HIGH (no delay) .....',
        rout.high()
        self.result("HIGH", rin.text_state)

        print 'LOW  (no delay) .....',
        rout.low()
        self.result("LOW", rin.text_state)

    def high(self, sleep_ms=0):
        self.rout.high()
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)

    def low(self, sleep_ms=0):
        self.rout.low()
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)

    def test_callbacks(self):
        delay = self.minimal_change_duration

        print '\nStarting callback tests\n'

        self.rin.changed = self.changed
        self.rin.rising = self.rising
        self.rin.falling = self.falling

        print "Raise. 100ms delay. Fall. 100ms delay.",

        self.high(100)
        self.low(100)

        self.result(['Rising', 'Changed', 'Falling', 'Changed'], self.call_stack)

        print "Raise, Fall, Raise (%dms delay)" % delay,
        self.call_stack = []

        self.high(delay)
        self.low(delay)
        self.high(delay)

        self.result(['Rising', 'Changed', 'Falling', 'Changed', 'Rising', 'Changed'], self.call_stack)

        print 'Fall, Raise, Fall (%dms delay)' % delay,
        self.call_stack = []

        self.low(delay)
        self.high(delay)
        self.low(delay)

        self.result(['Falling', 'Changed', 'Rising', 'Changed', 'Falling', 'Changed'], self.call_stack)

    def test_debouncing(self):
        delay = self.minimal_change_duration

        self.rin.bounce_interval = 20  # ms

        print '\nStarting debouncing tests\n'

        print "Raise, Fall, Raise (%dms delay)" % delay,
        self.call_stack = []

        self.high(delay)
        self.low(delay)
        self.high(delay)

        self.result(['Rising', 'Changed'], self.call_stack)

    def rising(self, current_time, state_duration):
        self.rising_called = {'current_time': current_time, 'state_duration': state_duration}
        self.call_stack.append('Rising')

    def falling(self, current_time, state_duration):
        self.falling_called = {'current_time': current_time, 'state_duration': state_duration}
        self.call_stack.append('Falling')

    def changed(self, current_state, current_time, state_duration):
        self.changed_called = {'current_state': current_state, 'current_time': current_time, 'state_duration': state_duration}
        self.call_stack.append('Changed')


if __name__ == "__main__":
    Rio.init()
    tester = RioTest(pin=13, pout=11)
    tester.test_regular()
    tester.test_callbacks()
    tester.test_debouncing()

    print '\n\nWaiting one second for all tests to finish and timer to stop'
    time.sleep(1)

    Rio.cleanup()
