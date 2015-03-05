import pjsua as pj

class SipAccountHandler(pj.AccountCallback):
    def __init__(self, account = None):
        pj.AccountCallback.__init__(self, account)

    def on_incoming_call(self, call):
        call.hangup(501, "")

    def on_reg_state(self):
        print "Registering: %s (%s" % (self.account.info().reg_status, self.account.info().reg_reason)
