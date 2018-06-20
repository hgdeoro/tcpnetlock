import logging
import sys
import time

from tcpnetlock.client import client
from tcpnetlock.cli import common

logger = logging.getLogger(__name__)


class Main(common.BaseMain):

    def add_app_arguments(self):
        self.parser.add_argument("lock_name")
        self.parser.add_argument("--host", default='localhost')
        self.parser.add_argument("--port", default=client.LockClient.DEFAULT_PORT, type=int)
        self.parser.add_argument("--client-id", default=None)
        self.parser.add_argument("--keep-alive", default=False, action='store_true')
        self.parser.add_argument("--keep-alive-secs", default=15, type=int)

    def main(self):
        lock_client = client.LockClient(self.args.host, self.args.port, client_id=self.args.client_id)
        lock_client.connect()
        granted = lock_client.lock(self.args.lock_name)
        if not granted:
            logger.debug("Lock not granted. Exiting...")
            sys.exit(9)

        if self.args.keep_alive:
            while True:
                logger.debug("Sleeping for %s... (after that, will send a keep-alive)", self.args.keep_alive_secs)
                time.sleep(self.args.keep_alive_secs)
                lock_client.keepalive()
        else:
            while True:
                logger.debug("Sleeping for an hour...")
                time.sleep(60 * 60)


def main():
    Main().run(args=sys.argv[1:])


if __name__ == '__main__':
    main()
