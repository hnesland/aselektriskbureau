import pjsua as pj

class SipTelephoneHandler(pj.CallCallback):
    def __init__(self, call = None):
        pj.CallCallback.__init__(self, call)

    def on_state(self):
        print "Call is %s" % self.call.info().state_text
        print "Last code = %s" % self.call.info().last_code
        print "Last reason = %s" % self.call.info().last_reason

    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            call_slot = self.call.info().conf_slot
            global TDaemon
            TDaemon.SipClient.pjlib.conf_connect(call_slot, 0)
            self.pjlib.conf_connect(0, call_slot)
