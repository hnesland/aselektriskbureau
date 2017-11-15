"""
This is the Daemon app that runs the a SIP phone on a Raspi with cool added
hardware, like an Astral wallphone or an AS Elektrisk Bureau.

Most of the threading is going to be via HardwareAbstractionLayer. That's
where we need to asynchronously wait for interactions from the user. SipClient
will logically also need to make asynchronous callbacks - 'we are connected,
stop playing the ringing tone.

WebServer is also going to have some callbacks.
"""


import Queue
import signal
import sys
import yaml


from phonedaemon.modules.Ringer import AlsaRinger
from phonedaemon.modules.HardwareAbstractionLayer \
    import AstralHAL, ElektriskHAL
from phonedaemon.modules.DialTimer import DialTimer
# from phonedaemon.modules.Webserver import Webserver
from phonedaemon.modules.SipClient import SipClient, CallHandler, \
    AccountHandler


CALLBACK_QUEUE = Queue.Queue()


class TelephoneDaemon(object):
    """
    This is the Daemon class, it sets up the sip connection and waits for
    events.
    """

    # pylint: disable=too-many-instance-attributes
    # This class needs attributes because I said so.

    config = None  # Contains config loaded from yaml.
    dialling_timeout = None  # How long off-hook before timeout
    reserved_numbers = {}  # Use for implementing app-hooks, e.g. Cortana

    entered_digits = ""  # Stores the number to be dialled.

    hal = None
    sipclient = None
    webserver = None
    timer = None
    ringer = None

    call_handler = None
    account_handler = None
    active_call = None
    registered = False

    ringing = False

    def __init__(self):
        print "[STARTUP]"

        signal.signal(signal.SIGINT, self.sigint_received)

        self.config = yaml.load(file("configuration_live.yaml", 'r'))

        if "diallingtimeout" in self.config:
            self.dialling_timeout = int(self.config["diallingtimeout"])
            print "[INFO] Using dialling timeout value:", self.dialling_timeout
        self.timer = DialTimer(timeout_length=self.dialling_timeout)

        self.ringer = AlsaRinger(sound_files=self.config["soundfiles"],
                                 alsa_devices=self.config["alsadevices"])

        self.hal = AstralHAL()
        self.hal.register_callbacks(self.digit_dialled,
                                    self.earpiece_replaced,
                                    self.earpiece_lifted)

        self.sipclient = SipClient()

        self.call_handler = CallHandler()
        self.account_handler = AccountHandler()

        self.sipclient.register_callbacks(self.call_handler,
                                          self.account_handler)

        call_callbacks = {
            "remote_busy": self.remote_busy,
            "connected": self.connected,
            "remote_hangup": self.remote_hangup,
            "call_dropped": self.call_dropped,
            "call_failed": self.call_failed
        }

        self.call_handler.register_callbacks(**call_callbacks)
        account_callbacks = {
            "registered": self.account_registered,
            "unregistered": self.unregistered,
            "incoming_call": self.incoming_call,
        }
        self.account_handler.register_callbacks(**account_callbacks)

        # self.sipclient.set_audio(self.config["alsadevices"]["earpiece"],
        #                          self.config["alsadevices"]["mouthpiece"])

        login_hostname = self.config["sip"]["hostname"]
        if login_hostname[0:4] != "sip:":
            login_hostname = "sip:" + login_hostname

        self.sipclient.login(self.config["sip"]["hostname"],
                             self.config["sip"]["username"],
                             self.config["sip"]["password"])

        self.entered_digits = self.config["sip"]["testnumber"]
        self.call_number()
        # self.webserver = Webserver(self)  # Currently locks thread?

        raw_input("Waiting.\n")

    def account_registered(self):
        """
        Set the phone active and ready for use once the SIP account has been
        successfully authenticated.
        """
        print "Welp. Logged in!"

    def unregistered(self):
        """
        Handle the situation where the SIP account has either failed to log
        in, or has logged out for some reason.
        """
        print "Welp. Unregistered."

    def earpiece_lifted(self):
        """
        The user has lifted the earpiece. Start dialling.
        """
        print "[INFO] Handset lifted."
        self.ringer.stop_ringer()
        if self.active_call:
            self.active_call.answer()
        else:
            self.entered_digits = ""
            # Begin wait for dialling state.

    def earpiece_replaced(self):
        """
        The user has replaced the earpiece. Whatever you're doing. stop.
        Stop all tones, close SIP call, stop dialling.
        """
        self.ringer.stop_earpiece()
        if self.active_call:
            self.active_call.hangup(487, "User hung up!")

    def call_number(self):
        """
        The user has entered a number. Send to SIP or handle internally.
        """
        print "[INFO] Calling number"
        self.sipclient.dial(self.entered_digits)
        # Log call to call log.

    def timeout_reached(self):
        """
        Check if the user has entered a number. Play the timeout tone.
        """
        if self.entered_digits:
            self.call_number()
            return None
        print "[INFO] Number not entered."
        self.ringer.play_error()

    def digit_dialled(self, digit):
        """
        The HAL has detected that a number has been dialled.
        Reset the timer and append the digit to the number to be dialled.
        """
        print "[INFO] Got digit:", digit
        self.entered_digits += digit
        self.timer.reset()

    def remote_busy(self):
        """
        The SIP user being called is engaged. Play busy tone and end.
        """
        self.ringer.play_busy()

    def incoming_call(self, call):
        """
        The SIP client reports an incoming call. Cancel dialling and play the
        ringtone. This should also trap the earpiece so that the call can be
        answered.
        """
        self.active_call = call
        self.ringer.play_ringer()

    def connected(self, call):
        """
        The SIP call in process is connected at the remote end. Stop playing
        the ringing tone.
        """
        self.ringer.stop_earpiece()
        self.active_call = call

    def remote_hangup(self):
        """
        The SIP client reports that the call terminated normally by remote
        hang up. Play the dialtone for retro fun.
        """
        if self.ringing:
            self.ringer.stop_ringer()
            return None
        self.ringer.stop_earpiece()
        if not self.active_call.is_valid()
            self.active_call = None

    def call_dropped(self):
        """
        The SIP client reports a dropped call.
        """
        self.ringer.stop_earpiece()
        if not self.active_call.is_valid()
            self.active_call = None

    def call_failed(self):
        """
        The SIP client returned an error on dialling. Stop all tones and play
        the error code.
        """
        self.ringer.play_error()
        if not self.active_call.is_valid()
            self.active_call = None

    def sigint_received(self, signal_name, frame):
        """
        Catch a signal from outside app (Ctrl-C) and shutdown cleanly.
        """
        print "[SIGNAL] Shutting down on:", signal_name
        if self.hal:
            self.hal.clean_exit()
        if self.sipclient:
            self.sipclient.logout()
        if self.ringer:
            self.ringer.clean_exit()
        sys.exit(0)


def main():
    """
    Start daemon and return exit code to command l
    """
    return TelephoneDaemon()


if __name__ == "__main__":
    main()
