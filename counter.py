import RPi.GPIO as GPIO
from rio import *

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
        Rio.init(GPIO.BOARD)

        self.rotation = Rin(self.pin_rotating)
        self.pulse = Rin(self.pin_pulse)

        self.rotation.changed(self.state_changed)
        self.rotations = 0
        self.events_start = None

    def state_changed(self, current_state, event_time, previous_state_duration):
        self.rotations += 1

        if not self.events_start:
            self.events_start = time.time() * 1000

            print "\n-----------------------------------------------------------------------------------------------"
            print "%2s | %16s | %6s[ms] | %6s[ms] | %5s | %s " % ('LP', 'Trigger', 'Abs. ', 'Length', 'Count', 'State')

        print "%2s | %16s | %6s[ms] | %6s[ms] | %5s | %s " % (
            self.rotations,
            'Rotation + %s' % current_state,
            event_time - self.events_start,
            previous_state_duration,
            '-',
            '-'
        )

c = Counter()

atexit.register(Rio.cleanup)

while True:
  time.sleep(1)
