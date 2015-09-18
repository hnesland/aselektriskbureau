import RPi.GPIO as GPIO
import rio

import atexit
from collections import OrderedDict
import collections

# IN  | OUT | Color
# 15  | 22  | Blue
# 16  | 23  | Green
# 18  | 24  | Red


class Counter:
    START = "Rotating START"
    FINISH = "Rotating FINISH"
    PULSE = "Pulse %d"

    pin_rotating = 16
    pin_pulse = 18

    pout_rotating = 23
    pout_pulse = 24

    bounce_time = 30  # ms
    return_threshold = 250  # ms

    rotations = 0

    def __init__(self):
        self.StartCounting()

    def Rotation(self, channel):
        self.rotating = not GPIO.input(channel)
        GPIO.output(self.pout_rotating, self.rotating)

        if self.rotating:
            # print "\nStarted rotation"
            self.trigger(self.START)
        else:
            self.trigger(self.FINISH)

            r = self.rotations
            number = r / 2 + r % 2
            # print "\nFinished rotation: %d" % self.rotations
            # print "Number: %d" % (number)

            Timer(0.5, self.TimingSummary).start()

        self.rotations = 0

    def NumberCounter(self, channel):
        time.sleep(0.01)  # 10ms

        self.trigger(self.PULSE % GPIO.input(channel))
        GPIO.output(self.pout_pulse, not GPIO.input(self.pin_pulse))

        if self.rotating and (GPIO.input(channel) == 1):
            self.rotations += 1

    def StartCounting(self):
        self.start_time = None
        self.triggers = OrderedDict()

    def trigger(self, name):
        t = int(round(time.time() * 1000))

        if self.start_time is None:
            self.start_time = t
            self.prev_time = t

        print "%2d | %16s | +%6dms | %6dms " % (self.rotations, name, t - self.prev_time, t - self.start_time)

        self.prev_time = t
        self.triggers[t] = name

    def TimingSummary(self):
        'Print timing of triggers captured'

        prev = 0
        c = 0

        c = collections.Counter()

        states = iter(['pre_start', 'pre_threshold', 'post_threshold', 'post_finish'])
        state = 'pre_start'

        # print "%2s | %16s | %6sms | %6sms | %5s | %s " % ('LP', 'Trigger', 'Rel. ', 'Abs. ', 'Count', 'State')
        for tt, trigger in self.triggers.iteritems():
            t = tt - self.start_time
            diff = t - prev

            if trigger == self.START:
                state = 'pre_threshold'
            if state == 'pre_threshold' and (diff > self.return_threshold):
                state = 'post_threshold'
            if state == 'post_threshold' and trigger == self.FINISH:
                state = 'post_finish'

            c['total'] += 1
            c[state] += 1

            # print "%2d | %16s | %6dms | %6dms | %d | %s " % (c['total'], trigger, diff, t, c[state], state)

            prev = t

            time.sleep(
                0.01)  # For some strange reason sometimes flushing doesn't work correctly :/ adding this delay to help it print properly.

        for k in states:
            print("%s: %d" % (k, c[k])),
        print("")

        self.StartCounting()

    def cleanup(self):
        GPIO.cleanup()


c = Counter()


def cleanup():
    print "Cleaning up"
    GPIO.cleanup()


atexit.register(cleanup)

while True:
  time.sleep(1)
