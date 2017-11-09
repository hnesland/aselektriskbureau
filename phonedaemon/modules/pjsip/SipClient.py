import pjsua as pj
from SipAccountHandler import SipAccountHandler
from SipTelephoneHandler import SipTelephoneHandler

class SipClient:
    hostname = ""

    def __init__(self):
        self.pjlib = pj.Lib()
        self.pjlib.init(log_cfg = pj.LogConfig(level = 4, callback = self.Log))
        print self.pjlib.enum_snd_dev()
        self.pjlib.set_snd_dev(2,1)
        self.transport = self.pjlib.create_transport(pj.TransportType.UDP)

    def Connect(self, hostname, username, password):
        self.pjlib.start()
        self.hostname = hostname
        self.acc_cfg = pj.AccountConfig(hostname, username, password)
        self.acc_cb = SipAccountHandler()
        self.acc = self.pjlib.create_account(self.acc_cfg, cb = self.acc_cb)

    def Dial(self, number):
        destination = "sip:%s@%s" % (number, self.hostname)
        self.current_call = self.acc.make_call(destination, SipTelephoneHandler())

    def Stop(self):
        self.pjlib.destroy()
        self.pjlib = None

    def Log(self, level, str, len):
        print "[DEBUG] %s" % str.rstrip("\n")

