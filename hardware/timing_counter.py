from rio import *

import atexit


# Module for testing the rotary dial timing, debouncing, etc.
#
# PINS
# IN  | OUT | Color  | Role     | Initial state
# 15  | 22  | Blue   | Rotation | High
# 16  | 23  | Green  | Pulse    | Low
# 18  | 24  | Red


class Counter:
    """
    Standalone module used for debugging rotary dial, choosing debouncing value, etc.
    Configured independently.
    """

    pin_rotating = 15
    pin_pulse = 16

    pout_rotating = 22
    pout_pulse = 23

    bounce_time = 10  # ms
    threshold = 100  # ms

    events = 0

    def __init__(self):
        Rio.init(GPIO.BOARD)

        b = 25

        self.rotation = Rin(self.pin_rotating, bounce_interval=b)
        self.pulse = Rin(self.pin_pulse, bounce_interval=b)

        self.rotation_led = Rout(self.pout_rotating)
        self.pulse_led = Rout(self.pout_pulse)

        self.rotation_led.set(self.rotation.state())
        self.pulse_led.set(self.pulse.state())

        self.rotation.changed = self.rotation_changed
        self.pulse.changed = self.pulse_changed

        self.events = 0
        self.events_start = None
        self.events_timer = None

        self.timer_lock = Lock()

        self.pulses = 0

        self.pulse_rest_state = self.pulse.text_state
        self.rotation_rest_state = self.rotation.text_state

        self.restart()

    def restart(self):
        print "\nPULSES: %d\n" % self.pulses

        self.events_start = None
        self.events_timer = None

        self.pulses = 0

        self.pulse_rest_state = self.pulse.text_state
        self.rotation_rest_state = self.rotation.text_state

    def rotation_changed(self, new_state, event_time, previous_state_duration):
        self.rotation_led.set(new_state)
        self.state_changed("Rotation", new_state, event_time, previous_state_duration)

    def pulse_changed(self, new_state, event_time, previous_state_duration):
        if new_state == 1:
            self.pulses += 1
        self.pulse_led.set(new_state)
        self.state_changed("Pulse", new_state, event_time, previous_state_duration)

    def state_changed(self, pin_name, new_state, event_time, previous_state_duration):
        try:
            self.events += 1

            self.timer_lock.acquire()

            if not self.events_start:
                self.events_start = event_time
                self.events = 1

                print "\n----------------------------------------------------------------------------------------------"
                print "%2s | %16s | %5s | %4s[ms] | %4s[ms] | %8s" % ('LP', 'Trigger', 'State', 'Time', 'Len', 'Pulses')

                print "%2d | %16s | %5s | %8d | %8d | %8d" % (0, 'Pulse', self.pulse_rest_state, 0, 0, 0)
                print "%2d | %16s | %5s | %8d | %8d | %8d" % (0, 'Rotation', self.rotation_rest_state, 0, 0, 0)

            text_state = "HIGH" if new_state else "LOW"
            print "%2d | %16s | %5s | %8d | %8d | %8d " % (
                self.events,
                pin_name,
                text_state,
                int(event_time - self.events_start),
                previous_state_duration,
                self.pulses
            )

            if self.events_timer:
                self.events_timer.cancel()
            self.events_timer = Timer(2, self.restart)
            self.events_timer.start()
        finally:
            self.timer_lock.release()


c = Counter()

atexit.register(Rio.cleanup)

while True:
    time.sleep(1)
