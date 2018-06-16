import collections
import logging
import re
import socketserver
import threading
import time

from tcpnetlock import utils

"""
This implement a very simple network lock server based on just TCP.

The server listen for connections, reads the socket for a '\n' terminated line.
The received string is used as lock name.

If the lock is granted, it is valid until the client release it, or until the TCP connection is closed.

If the lock can't be granted, a response is sent to the client and the TCP connection is closed.


Detail of the current implementation:

    1. SERVER accept TCP connection
    2. CLIENT send the lock name (utf-8 encoded), like: 'lock-name\n'
    3. SERVER tries to acquire the lock
        a. if lock was granted, returns 'ok\n' to the client and the TCP connections is KEPT OPEN
            - the LOCK remains granted until:
               + the client release it, sending 'release\n' to the server (and the TCP connection is CLOSED)
               + the client closes the TCP connection
               + for some reason the TCP connection is lost
        b. if lock was NOT granted, returns 'failed\n' to the client and the TCP connection is immediately CLOSED
"""

logger = logging.getLogger(__name__)


RESPONSE_OK = 'ok'
RESPONSE_ERR = 'err'
RESPONSE_LOCK_FAILED = 'failed'
RESPONSE_RELEASED = 'released'
RESPONSE_SHUTTING_DOWN = 'shutting-down'
RESPONSE_PONG = 'pong'
RESPONSE_STILL_ALIVE = 'alive'

ACTION_RELEASE = 'release'
ACTION_SERVER_SHUTDOWN = '.server-shutdown'
ACTION_PING = '.ping'
ACTION_KEEPALIVE = '.keepalive'

VALID_LOCK_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')
VALID_CLIENT_ID_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


class Holder:
    def __init__(self):
        self._lock = self._lock = threading.Lock()
        self._lock_name = None
        self._timestamp = None
        self._client_id = None

    def try_acquire(self, lock_name, client_id):
        granted = self._lock.acquire(blocking=False)
        if granted:
            self._timestamp = time.time()
            self._client_id = client_id
            self._lock_name = lock_name
        return granted

    def release(self):
        self._lock.release()

    def __str__(self):
        return "Lock '{name}', client '{client}', age: {age}".format(
            name=self._lock_name, client=self._client_id, age=int(time.time() - self._timestamp))


class LockServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, host='localhost', port=9999):
        super().__init__((host, port), TCPHandler)


class TCPHandler(socketserver.BaseRequestHandler):
    GLOBAL_LOCK = threading.Lock()
    LOCKS = collections.defaultdict(Holder)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock_name = None

    def _get_line(self) -> str:
        """
        Reads (blocking) until we got a lock name
        :return: lock name
        """
        binary_data = bytearray()
        while True:
            lock_name = utils.try_get_line(self.request, binary_data)
            if lock_name:
                return lock_name

    def _handle_lock(self, holder: Holder):
        try:
            try:
                self._real_handle_lock(holder)
            except utils.ClientDisconnected:
                logger.info("[%s] Client disconnected", self._lock_name)
        finally:
            holder.release()

    def _send(self, message):
        self.request.send((message + '\n').encode())

    def _real_handle_lock(self, holder: Holder):
        """
        While control is in this method, the lock is held
        """
        self._send(RESPONSE_OK)
        binary_data = bytearray()
        while True:
            action = utils.try_get_line(self.request, binary_data, timeout=1.0)
            if action:
                logger.info("Action: '%s' for lock %s", action, holder)
                binary_data = bytearray()
                if action == ACTION_RELEASE:
                    logger.debug("Releasing lock: %s", holder)
                    self._send(RESPONSE_RELEASED)
                    self.request.close()
                    # FIXME: at this point we send OK to the client, but internally the lock is STILL HELD
                    return
                if action == ACTION_KEEPALIVE:
                    logger.debug("Received keepalive from client. Lock: %s", holder)
                    self._send(RESPONSE_STILL_ALIVE)
                else:
                    logger.debug("Unknown action '%s' for lock: %s", action, holder)

    def _handle_server_shutdown(self):
        # FIXME: assert connections came from localhost
        self._send(RESPONSE_SHUTTING_DOWN)  # FIXME: what if client had closed the socket?
        self.request.close()
        self.server.shutdown()

    def _handle_ping(self):
        self._send(RESPONSE_PONG)  # FIXME: what if client had closed the socket?
        self.request.close()

    def _handle_invalid_lock_hame(self):
        self._send(RESPONSE_ERR + ':invalid lock name')  # FIXME: what if client had closed the socket?
        self.request.close()

    def handle(self):
        try:
            line = self._get_line()
        except utils.ClientDisconnected:
            logger.info("Client disconnected")
            self.request.close()
            return

        logger.debug("Received line: '%s'", line)

        if line == ACTION_SERVER_SHUTDOWN:
            self._handle_server_shutdown()
            return

        if line == ACTION_PING:
            self._handle_ping()
            return

        # Not a special string? Then it's a lock name (plus optional client-id)
        tokens = line.split(':')
        try:
            (self._lock_name, client_id) = tokens
        except ValueError:
            (self._lock_name, client_id) = tokens[0], None

        if not VALID_LOCK_NAME_RE.match(self._lock_name):
            self._handle_invalid_lock_hame()
            return

        # Get the holder
        self.GLOBAL_LOCK.acquire()
        try:
            lock_holder = self.LOCKS[self._lock_name]
        finally:
            self.GLOBAL_LOCK.release()

        # Lock it
        granted = lock_holder.try_acquire(self._lock_name, client_id)
        if granted:
            logger.debug("Got lock :)")
            self._handle_lock(lock_holder)
        else:
            logger.debug("Couldn't get lock :(")
            self._send(RESPONSE_LOCK_FAILED)  # FIXME: what if client had closed the socket?

        self.request.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", default='localhost')
    parser.add_argument("--port", default=9999, type=int)
    parser.add_argument("--debug", default=False, action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    with LockServer(args.listen, args.port) as server:
        logging.info("Started listening on %s:%s", args.listen, args.port)
        server.serve_forever()


if __name__ == '__main__':
    main()
