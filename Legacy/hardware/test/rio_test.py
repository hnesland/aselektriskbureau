import time
from hardware.rio import Rio, Rin, Rout

__author__ = 'swistak'


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

    def test(self, method):
        print ("----------------------------------------------------------------------------------------------------")

        print 'Starting %s tests.\n' % method
        Rio.init()

        self.rin = Rin.get(self.pin)
        self.rout = Rout.get(self.pout)

        self.start_time = 0
        self.call_stack = []

        getattr(self, 'test_'+method)()

        print '\nFinishing %s tests.\n' % method
        Rio.cleanup()

    def test_regular(self):
        print 'HIGH for 1 second (check if led is on).'
        self.rout.high()
        time.sleep(1)

        print 'HIGH (10ms delay) ...',
        self.rout.high()
        time.sleep(0.01)
        self.result("HIGH", self.rin.text_state)

        print 'LOW  (10ms delay) ...',
        self.rout.low()
        time.sleep(0.01)
        self.result("LOW", self.rin.text_state)

        print 'HIGH (1ms delay) ....',
        self.rout.high()
        time.sleep(0.001)
        self.result("HIGH", self.rin.text_state)

        print 'LOW  (1ms delay) ....',
        self.rout.low()
        time.sleep(0.001)
        self.result("LOW", self.rin.text_state)

        print 'HIGH (no delay) .....',
        self.rout.high()
        self.result("HIGH", self.rin.text_state)

        print 'LOW  (no delay) .....',
        self.rout.low()
        self.result("LOW", self.rin.text_state)

    def test_callbacks(self):
        delay = self.change_duration

        print '\nStarting callback tests\n'

        self.low(delay)

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
        print '\nStarting debouncing tests\n'

        self.rin.rising = self.rising
        self.rin.falling = self.falling

        self.debounce_sequence("10101__", ['Rising'])
        self.debounce_sequence("01010__", ['Falling'], start='HIGH')

        self.debounce_sequence('101_0__', [])
        self.debounce_sequence('1010___', [])

        self.debounce_sequence('101_010__', [])
        self.debounce_sequence('1010__1__', ['Rising'])

        overhead = 2  # ms

        print "Testing timing"

        def period():
            if self.rising_called is not None:
              return int(round(self.rising_called['state_duration'] / (self.change_duration + overhead))) + 1

        self.debounce_sequence('1__', ['Rising'])
        self.result(1, period(), 'Period 1')

        self.debounce_sequence('01__', ['Rising'])
        self.result(2, period(), 'Period 2')

        self.debounce_sequence('101__', ['Rising'])
        self.result(3, period(), 'Period 3')

        self.debounce_sequence('10101__', ['Rising'])
        self.result(5, period(), 'Period 5')

        self.debounce_sequence('101__', ['Rising'])

        self.rin.rising = None
        self.rin.falling = None
        self.rin.changed = self.changed

        self.debounce_sequence('101__', ['Changed'])
        self.result(1, self.changed_called['new_state'], 'State change')

    # Test callbacks

    def rising(self, event_time, state_duration):
        self.rising_called = {'event_time': event_time - self.start_time, 'state_duration': state_duration}
        self.call_stack.append('Rising')

    def falling(self, event_time, state_duration):
        self.falling_called = {'event_time': event_time - self.start_time, 'state_duration': state_duration}
        self.call_stack.append('Falling')

    def changed(self, new_state, event_time, state_duration):
        self.changed_called = {'new_state': new_state, 'event_time': event_time - self.start_time,
                               'state_duration': state_duration}
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

    def bounce_sequence(self, sequence, expected, delay=change_duration, start="LOW", wait_after=0):
        print sequence, '->', expected,

        if start == "LOW":
            self.low(delay)
        elif start == "HIGH":
            self.high(delay)

        self.rin.reset()
        self.call_stack = []
        self.changed_called = self.rising_called = self.falling_called = None
        self.start_time = self.rin.ms_time()

        for e in sequence:
            if e == 'R' or e == '1':
                self.high(delay)
            elif e == 'L' or e == '0':
                self.low(delay)
            else:
                time.sleep(delay / 1000.0)

        if wait_after > 0:
            time.sleep(wait_after / 1000.0)

        self.result(expected, self.call_stack)

    def debounce_sequence(self, sequence, expected, delay=change_duration, start="LOW"):
        if start == "LOW":
            self.low(delay)
        elif start == "HIGH":
            self.high(delay)

        self.rin.bounce_interval = 4 * self.change_duration - 1  # ms
        self.bounce_sequence(sequence, expected, delay, start=None, wait_after=self.rin.bounce_interval)
        self.rin.bounce_interval = 0

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
    tester = RioTest(pin=13, pout=11)

    tester.test("regular")
    tester.test("callbacks")
    tester.test("debouncing")

    print '\n\nDone.'

