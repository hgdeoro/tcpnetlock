import argparse
import logging
import sys
import time

from tcpnetlock import client

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lock_name")
    parser.add_argument("--host", default='localhost')
    parser.add_argument("--port", default=client.LockClient.DEFAULT_PORT, type=int)
    parser.add_argument("--client-id", default=None)
    parser.add_argument("--keep-alive", default=False, action='store_true')
    parser.add_argument("--keep-alive-secs", default=15, type=int)
    parser.add_argument("--debug", default=False, action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    lock_client = client.LockClient(args.host, args.port, client_id=args.client_id)
    lock_client.connect()
    granted = lock_client.lock(args.lock_name)
    if not granted:
        logger.debug("Lock not granted. Exiting...")
        sys.exit(9)

    if args.keep_alive:
        while True:
            logger.debug("Sleeping for %s... (after that, will send a keep-alive)", args.keep_alive_secs)
            time.sleep(args.keep_alive_secs)
            lock_client.keepalive()
    else:
        while True:
            logger.debug("Sleeping for an hour...")
            time.sleep(60 * 60)


if __name__ == '__main__':
    main()
