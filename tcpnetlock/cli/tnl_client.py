import logging
import sys
import time

from tcpnetlock.client import client
from tcpnetlock.cli import common
from tcpnetlock.common import ClientDisconnected

logger = logging.getLogger(__name__)


ERR_CONNECTION_REFUSED = 2
ERR_CONNECTION_FAILED = 3
ERR_UNKNOWN = 4

ERR_TCP_DISCONNECT_WHILE_HOLDING_LOCK = 122
ERR_LOG_NOT_GRANTED = 123


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

        try:
            lock_client.connect()
        except ConnectionRefusedError as err:
            logger.debug("ConnectionRefusedError", exc_info=True)
            print(str(err), file=sys.stderr)
            sys.exit(ERR_CONNECTION_REFUSED)
        except BaseException as err:
            logger.debug("Can't connect", exc_info=True)
            print(str(err), file=sys.stderr)
            sys.exit(ERR_CONNECTION_FAILED)

        try:
            granted = lock_client.lock(self.args.lock_name)
            if not granted:
                logger.debug("Lock '%s' not granted. Exiting...", self.args.lock_name)
                print("ERROR: lock '{lock}' not granted by server".format(lock=self.args.lock_name), file=sys.stderr)
                sys.exit(ERR_LOG_NOT_GRANTED)

            if self.args.keep_alive:
                while True:
                    logger.info("Sleeping for %s... (after that, will send a keep-alive)", self.args.keep_alive_secs)
                    time.sleep(self.args.keep_alive_secs)
                    lock_client.keepalive()
            else:
                while True:
                    logger.debug("Checking connection...")
                    try:
                        lock_client.check_connection()
                    except ClientDisconnected as err:
                        logger.debug("Unexpected disconnection while holding the lock '%s'. "
                                     "Server was killed?", self.args.lock_name)
                        print("ERROR: Unexpected disconnection while holding the lock '{lock}'. "
                              "Server was killed?".format(lock=self.args.lock_name),
                              file=sys.stderr)
                        sys.exit(ERR_TCP_DISCONNECT_WHILE_HOLDING_LOCK)

                    time.sleep(5)

        except SystemExit as err:
            sys.exit(err.code)

        except BaseException as err:
            logger.debug("Error while getting or having the lock", exc_info=True)
            print(str(err), file=sys.stderr)
            sys.exit(ERR_UNKNOWN)
        finally:
            lock_client.close()


def main():
    Main().run(args=sys.argv[1:])


if __name__ == '__main__':
    main()
