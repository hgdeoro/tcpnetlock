import argparse
import logging

from tcpnetlock import server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", default='localhost')
    parser.add_argument("--port", default=server.LockServer.DEFAULT_PORT, type=int)
    parser.add_argument("--debug", default=False, action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    with server.LockServer(args.listen, args.port) as lock_server:
        logging.info("Started listening on %s:%s", args.listen, args.port)
        lock_server.serve_forever()


if __name__ == '__main__':
    main()
