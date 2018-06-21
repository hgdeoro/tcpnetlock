import logging
import sys

from tcpnetlock.server import server
from tcpnetlock.cli import common


EXIT_SERVER_BIND_ERROR = 2
EXIT_HANDLING_REQUESTS_ERROR = 3


class Main(common.BaseMain):

    def add_app_arguments(self):
        self.parser.add_argument("--listen", default='localhost')
        self.parser.add_argument("--port", default=server.TCPServer.DEFAULT_PORT, type=int)

    def main(self):
        logging.info("Started server listening on %s:%s", self.args.listen, self.args.port)
        try:
            lock_server = server.TCPServer(self.args.listen, self.args.port)
        except BaseException as err:
            logging.debug('Error while bind()ing...', exc_info=True)
            print(str(err) or 'Error detected while creating server', file=sys.stderr)
            sys.exit(EXIT_SERVER_BIND_ERROR)

        try:
            lock_server.serve_forever()
        except BaseException as err:
            logging.debug('Error while handling requests...', exc_info=True)
            print(str(err) or 'Error while handling requests', file=sys.stderr)
            sys.exit(EXIT_HANDLING_REQUESTS_ERROR)


def main():
    Main().run(args=sys.argv[1:])


if __name__ == '__main__':
    main()
