"""
This is the Daemon app that runs the a SIP phone on a Raspi with cool added
hardware, like an Astral wallphone or an AS Elektrisk Bureau.
"""


import os
import Queue
import signal
import sys
import yaml

from phonedaemon.modules.Ringtone import Ringtone
from phonedaemon.modules.RotaryDial import RotaryDial
from phonedaemon.modules.Webserver import Webserver
from phonedaemon.modules.DialTimer import DialTimer
from phonedaemon.modules.linphone import Wrapper

# alternative SIP-implementation
# from modules.pjsip.SipClient import SipClient


CALLBACK_QUEUE = Queue.Queue()


class TelephoneDaemon(object):
    """
    This is the Daemon class, it sets up the sip connection and waits for
    events.
    """
    config = None  # Contains config loaded from yaml.
    dialling_timeout = None  # How long off-hook before tim

    dial_number = ""  # Stores the number to be dialled.

    off_hook = False  # Flag: Is the earpiece on or off the hook?

    app_rotary_dial = None
    app_sip_client = None
    app_webserver = None
    app_timer = None
    app_ringer = None

    def __init__(self):
        print "[STARTUP]"

        self.config = yaml.load(file("configuration.yaml", 'r'))

        if "diallingtimeout" in self.config:
            self.dialling_timeout = int(self.config["diallingtimeout"])
            print "[INFO] Using dialling timeout value:", self.dialling_timeout

        self.app_timer = DialTimer(timeout_length=self.dialling_timeout)

        self.off_hook
        signal.signal(signal.SIGINT, self.OnSignal)

        # TODO: Select tone/hardware ring when latter is implemented.
        self.app_ringer = Ringtone(self.config)

        # This is to indicate boot complete. Not very realistic, but fun.
        # self.Ringtone.playfile(config["soundfiles"]["startup"])

        # Rotary dial
        self.RotaryDial = RotaryDial()
        self.RotaryDial.register_callback(NumberCallback=self.got_digit,
                                         OffHookCallback=self.off_hook,
                                         OnHookCallback=self.on_hook,
                                         OnVerifyHook=self.on_verify_hook)

        # TODO: Way to select SIP backend programmatically/flagly.

        self.app_sip_client = Wrapper.Wrapper()
        self.app_sip_client.StartLinphone()
        self.app_sip_client.SipRegister(self.config["sip"]["username"],
                                        self.config["sip"]["hostname"],
                                        self.config["sip"]["password"])
        self.app_sip_client.RegisterCallbacks(OnIncomingCall=self.on_incoming_call,
                                              OnOutgoingCall=self.on_outgoing_call,
                                              OnRemoteHungupCall=self.on_remote_hungup_call,
                                              OnSelfHungupCall=self.on_self_hungup_call)

        # Start SipClient thread
        self.app_sip_client.start()

        # Web interface to enable remote configuration and debugging.
        self.app_webserver = Webserver(self)

        raw_input("Waiting.\n")

    def on_hook(self):
        print "[PHONE] On hook"
        self.offHook = False
        self.Ringtone.stophandset()
        # Hang up calls
        if self.app_sip_client is not None:
            self.app_sip_client.SipHangup()

    def off_hook(self):
        print "[PHONE] Off hook"
        self.offHook = True
        # Reset current number when off hook
        self.dial_number = ""

        self.app_timer.start()

        # TODO: State for ringing, don't play tone if ringing :P
        print "Try to start dialtone"
        self.Ringtone.starthandset(self.config["soundfiles"]["dialtone"])

        self.Ringtone.stop()
        if self.app_sip_client is not None:
            self.app_sip_client.SipAnswer()

    def on_verify_hook(self, state):
        if not state:
            self.offHook = False
            self.Ringtone.stophandset()

    def on_incoming_call(self):
        print "[INCOMING]"
        self.Ringtone.start()

    def on_outgoing_call(self):
        print "[OUTGOING] "

    def on_remote_hungup_call(self):
        print "[HUNGUP] Remote disconnected the call"
        # Now we want to play busy-tone..
        self.Ringtone.starthandset(self.config["soundfiles"]["busytone"])

    def on_self_hungup_call(self):
        print "[HUNGUP] Local disconnected the call"

    def got_digit(self, digit):
        print "[DIGIT] Got digit: %s" % digit
        self.Ringtone.stophandset()
        self.dial_number += str(digit)
        print "[NUMBER] We have: %s" % self.dial_number

        self.app_timer.reset()  # Reset the end-of-dialling clock.

        """
        # Shutdown command, since our filesystem isn't read only (yet?)
        # This hopefully prevents dataloss.
        # TODO: stop rebooting..

        Commented for probable removal. I may add a reboot command to the web
        interface, but the device is set up for SSH, and I don't forsee a
        situation where a clean reboot is needed but ssh is inaccessible.

        if self.dial_number == "0666":
            self.Ringtone.playfile(self.config["soundfiles"]["shutdown"])
            os.system("halt")
        """

    def on_timer_end(self):
        print "[OFFHOOK TIMEOUT]"
        if self.dial_number:
            print "[PHONE] Dialling number: %s" % self.dial_number
            self.app_sip_client.SipCall(self.dial_number)
        self.dial_number = ""

    def OnSignal(self, signal, frame):
        print "[SIGNAL] Shutting down on %s" % signal
        self.RotaryDial.StopVerifyHook()
        self.app_sip_client.StopLinphone()
        sys.exit(0)


def main():
    TDaemon = TelephoneDaemon()


if __name__ == "__main__":
    main()
