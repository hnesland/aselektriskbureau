"""
This needs waaaaay fleshing out. This should provide a web config page for at
least the sip and audio device parts (ringer volume?) and a web dialler/API
for remotely triggering an outward call without using the rotary interface.

Nice to haves:
  * Call logging with export to CSV.
  * wifi config over web.
  * Diagnostic controls.
"""


import tornado.web
from tornado.options import define, options, parse_command_line


define("port", default=8080, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")


class MainHandler(tornado.web.RequestHandler):
    """
    Handle requests from remote clients.
    """
    def get(self):
        """
        Respond to a GET request.
        """
        self.render("../web/index.html")

class Webserver(object):
    """
    This class runs the actual server object.
    """
    app = None
    telephone = None

    def __init__(self, telephone):
        parse_command_line()

        self.telephone = telephone

        self.app = tornado.web.Application(
            [
                (r"/", MainHandler)
            ]
            )

        self.app.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
