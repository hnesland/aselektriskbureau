import atexit
from rio import *
import config


class RotaryDial:
    """
    Provides a way to capture the rotary dial pulses on Tel-Art Via Reggio (model I'm having).

    Calls a callback with number between 0 and 9 when rotation is finished.

    In idle state the _rotation_ pin is pulled **high**, while _pulse_ pin is **low**.
    When rotation starts each **high** on pulse pin is counted.
    Rotation finishes when _rotation_ pin is pulled **high** again, this can happen before last pulse is pulled **low**,
    for that reason we're counting pulses on **high**.

    The state of pins can be displayed on two leds to give a visual help while debugging/repairing.

    Pin configuration can be set in `configuration.py` file. Pin pairs 11&13, 13&15, 15&16 or 16&18 are recommended
    because they are adjoined and not assigned to any other functions.
    """

    bounce_time = 25  # ms

    def __init__(self, rotation_finished, rotation_problem=None):
        """
        :param rotation_finished: Callback accepting one argument [number] from 0 to 9. Called when rotation is finished
        :param rotation_problem: Callback accepting one argument [number] of pulses that were outside 1-10 scope.
        :return:
        """
        Rio.init(GPIO.BOARD)

        self.rotation = Rin(config.PIN_IN_ROTATING, bounce_interval=self.bounce_time)
        self.pulse = Rin(config.PIN_IN_PULSE, bounce_interval=self.bounce_time)

        self.rotation_led = Rout(config.PIN_OUT_ROTATING)
        self.pulse_led = Rout(config.PIN_OUT_PULSE)

        self.rotation_led.set(not self.rotation.state())
        self.pulse_led.set(self.pulse.state())

        self.rotation.changed = self.rotation_changed
        self.pulse.changed = self.pulse_changed

        self.pulses = 0

        self.rotation_finished = rotation_finished
        self.rotation_problem = rotation_problem

    def pulse_changed(self, new_state, event_time, previous_state_duration):
        self.pulse_led.set(new_state)
        if new_state == 1:
            self.pulses += 1

    def rotation_changed(self, new_state, event_time, previous_state_duration):
        self.rotation_led.set(not new_state)

        if new_state == 0:
            # rotation_started
            self.pulses = 0
        else:
            if self.pulses == 0 or self.pulses > 10:
                if self.rotation_problem:
                    self.rotation_problem(self.pulses)
            else:
                self.rotation_finished(self.pulses % 10)


atexit.register(Rio.cleanup)

if __name__ == "__main__":
    numbers = []
    working = True


    def finished(number):
        global working

        print number,
        numbers.append(number)
        if len(numbers) > 1 and numbers[-1] == 0 and numbers[-2] == 0:
            print "\nExiting"
            working = False


    RotaryDial(finished)

    print "Dial two 0 to exit. (or ctrl+c)"
    while working:
        time.sleep(0.1)
