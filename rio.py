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

    @classmethod
    def cleanup(cls):
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
    def __init__(self, number):
        self.falling = None
        self.rising = None
        self.changed = None

        self.number = number
        self.bounce_interval = 0  # ms

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

        Tricky part is there's not real guarantee that there cannot be two falling events in a row.
        """

        if not self.bounce_timer:
            if new_state != self.current_state:
                self.bounce_timer = Timer(self.bounce_interval / 1000.0, self.event, [change_time, new_state])
                self.bounce_timer.start()
        else:
            if new_state == self.current_state:
                self.bounce_timer.cancel()
                self.bounce_timer = None

    def event(self, change_time, new_state):
        """
        Processes event, including debouncing and measurement of previous state length.
        """

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
            self.changed(self.current_state, change_time, state_duration)

    def state(self):
        return GPIO.input(self.number)

    @property
    def text_state(self):
        return "HIGH" if self.state() else "LOW"

    def ms_time(self):
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

    change_duration = 5  # ms.

    def __init__(self, **pins):
        """
            :param pin: Pin number for input (numbered by board number or BCM depending on value passed to init()
            :param pout: Pin number for output (numbered by board number or BCM depending on value passed to init()
        """

        self.pin = pins['pin']
        self.pout = pins['pout']

        self.rin = None
        self.rout = None

        self.rising_called = None
        self.falling_called = None
        self.changed_called = None

        self.start_time = 0

        self.call_stack = []

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

        Rio.cleanup()

    def test_callbacks(self):
        self.rin = Rin.get(self.pin)
        self.rout = Rout.get(self.pout)

        delay = self.change_duration

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

        Rio.cleanup()

    def test_debouncing(self):
        self.rin = Rin.get(self.pin)
        self.rout = Rout.get(self.pout)

        print '\nStarting debouncing tests\n'

        self.rin.bounce_interval = 4 * self.change_duration - 1  # ms

        self.rin.rising = self.rising
        self.rin.falling = self.falling

        self.bounce_sequence("10101______", ['Rising'])
        self.bounce_sequence("01010______", ['Falling'], start='HIGH')

        self.bounce_sequence('101_0______', [])
        self.bounce_sequence('1010_______', [])

        self.bounce_sequence('101_010____', [])
        self.bounce_sequence('1010__1____', ['Rising'])

        self.rin.rising = None
        self.rin.falling = None
        self.rin.changed = self.changed

        self.bounce_sequence('101____', ['Changed'])
        self.result(1, self.changed_called['new_state'], 'State change')

        overhead = 2  # ms

        print "Testing timing"

        def period():
            return int(round(self.changed_called['state_duration'] / (self.change_duration + overhead))) + 1

        self.bounce_sequence('1____', ['Changed'])
        self.result(1, period(), 'Period 1')
        self.bounce_sequence('01____', ['Changed'])
        self.result(2, period(), 'Period 2')
        self.bounce_sequence('101____', ['Changed'])
        self.result(3, period(), 'Period 3')
        self.bounce_sequence('10101____', ['Changed'])
        self.result(5, period(), 'Period 5')

        self.bounce_sequence('101____', ['Changed'])
        self.result(1, self.changed_called['new_state'], 'State')

        Rio.cleanup()

    # Test callbacks

    def rising(self, event_time, state_duration):
        self.rising_called = {'event_time': event_time - self.start_time, 'state_duration': state_duration}
        self.call_stack.append('Rising')

    def falling(self, event_time, state_duration):
        self.falling_called = {'event_time': event_time - self.start_time, 'state_duration': state_duration}
        self.call_stack.append('Falling')

    def changed(self, new_state, event_time, state_duration):
        self.changed_called = {'new_state': new_state, 'event_time': event_time - self.start_time, 'state_duration': state_duration}
        self.call_stack.append('Changed')

    # Helpers.

    def high(self, sleep_ms=0):
        self.rout.high()
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)

    def low(self, sleep_ms=0):
        self.rout.low()
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)

    def bounce_sequence(self, sequence, expected, delay=change_duration, start="LOW"):
        print sequence, '->', expected,

        if start == "LOW":
            self.low()
        else:
            self.high()

        self.rin.reset()
        self.call_stack = []
        self.start_time = self.rin.ms_time()

        for e in sequence:
            if e == 'R' or e == '1':
                self.high(delay)
            elif e == 'L' or e == '0':
                self.low(delay)
            else:
                time.sleep(delay / 1000.0)

        self.result(expected, self.call_stack)

    @staticmethod
    def result(expected, actual, comment=''):
        ok = '\033[92m'
        fail = '\033[91m'
        exp = '\033[93m'
        end = '\033[0m'

        if expected == actual:
            print comment, ok, actual, end
        else:
            print comment, 'Got', fail, actual, end, "Expected", exp, expected, end


if __name__ == "__main__":
    Rio.init()
    tester = RioTest(pin=13, pout=11)

    # tester.test_regular()
    # tester.test_callbacks()
    tester.test_debouncing()

    print '\n\nWaiting one second for all tests to finish and timer to stop'
    time.sleep(1)

    # Rio.cleanup() # we're cleaning up after each test now.
