import tornado.web
import os.path
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("../web/index.html")

class Webserver:
    app = None
    Telephone = None

    def __init__(self, Telephone):
        parse_command_line()
        
        self.Telephone = Telephone

        self.app = tornado.web.Application(
            [
                (r"/", MainHandler)
            ]
            )

        self.app.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
