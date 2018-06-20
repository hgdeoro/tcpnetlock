import logging
import sys

from tcpnetlock.server import server
from tcpnetlock.cli import common


class Main(common.BaseMain):

    def add_app_arguments(self):
        self.parser.add_argument("--listen", default='localhost')
        self.parser.add_argument("--port", default=server.TCPServer.DEFAULT_PORT, type=int)

    def main(self):
        logging.info("Started server listening on %s:%s", self.args.listen, self.args.port)
        with server.TCPServer(self.args.listen, self.args.port) as lock_server:
            lock_server.serve_forever()


def main():
    Main().run(args=sys.argv[1:])


if __name__ == '__main__':
    main()
