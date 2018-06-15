import collections
import logging
import socketserver
import threading

from tcpnetlock import utils


"""
This implement a very simple network lock server based on just TCP.

The current implementation:

    1. SERVER accept connection
    2. CLIENT send the string 'lock-name\n'
    3. SERVER tries to acquire the lock
        - if lock is acquired, returns 'ok\n' to the client and the TCP connections is KEPT OPEN
        - if lock is NOT acquired, returns 'err\n' to the client and the TCP connection is CLOSED
"""

logger = logging.getLogger(__name__)

GLOBAL_LOCK = threading.Lock()

LOCKS = collections.defaultdict(threading.Lock)

RESPONSE_OK = 'ok\n'.encode()
RESPONSE_ERR = 'err\n'.encode()

SERVER_SHUTDOWN = '.SERVER_SHUTDOWN'
PING = '.PING'


class LockServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, host, port):
        super().__init__((host, port), TCPHandler)


class TCPHandler(socketserver.BaseRequestHandler):

    def _get_lockname(self) -> str:
        """
        Reads (blocking) until we got a lock name
        :return: lock name
        """
        binary_data = bytearray()
        while True:
            lock_name = utils.try_get_line(self.request, binary_data)
            if lock_name:
                return lock_name

    def _handle_lock(self, lock):
        try:
            self._real_handle_lock(lock)
        finally:
            lock.release()

    def _real_handle_lock(self, lock):
        """
        While control is in this method, the lock is held
        """
        self.request.send(RESPONSE_OK)
        binary_data = bytearray()
        while True:
            action = utils.try_get_line(self.request, binary_data, timeout=1.0)
            logger.debug("action: '%s'", action)
            if action:
                binary_data = bytearray()
                if action == 'release':
                    logger.debug("Releasing lock")
                    self.request.close()
                    return
                else:
                    logger.debug("Unknown action: '%s'", action)

    def _handle_server_shutdown(self):
        # FIXME: assert connections came from localhost
        self.request.send('shutting-down\n'.encode())
        self.request.close()
        self.server.shutdown()

    def _handle_ping(self):
        self.request.send('pong\n'.encode())
        self.request.close()

    def handle(self):
        lock_name = self._get_lockname()
        logger.debug("lock_name: '%s'", lock_name)

        if lock_name == SERVER_SHUTDOWN:
            self._handle_server_shutdown()
            return

        if lock_name == PING:
            self._handle_ping()
            return

        # Not a special string? Then it's a lock name
        GLOBAL_LOCK.acquire()
        try:
            lock = LOCKS[lock_name]
        finally:
            GLOBAL_LOCK.release()

        locked = lock.acquire(blocking=False)
        if locked:
            logger.debug("Got lock :)")
            self._handle_lock(lock)
        else:
            logger.debug("Couldn't get lock :(")
            self.request.send(RESPONSE_ERR)

        self.request.close()


def main():
    logging.basicConfig(level=logging.DEBUG)
    host, port = "localhost", 9999

    with LockServer(host, port) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
