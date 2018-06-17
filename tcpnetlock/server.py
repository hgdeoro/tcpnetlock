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

If the lock can't be granted (it's being held by another client), a response is sent and the TCP connection is closed.


The simplest way to use:

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

VALID_CHARS_IN_LOCK_NAME_RE = re.compile(r'[a-zA-Z0-9_-]')


class Lock:
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


class Action:
    def __init__(self, action: str, params: dict):
        self.action = action
        self.params = params


class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    DEFAULT_PORT = 7654

    def __init__(self, host='localhost', port=DEFAULT_PORT):
        super().__init__((host, port), TCPHandler)


class BaseTCPHandler(socketserver.BaseRequestHandler):
    # FIXME: rename to readline()
    # FIXME: use socket.makefile()
    def _get_line(self) -> str:
        """
        Reads (blocking) until we got a line
        :return: lock name
        """
        binary_data = bytearray()
        while True:
            lock_name = utils.try_get_line(self.request, binary_data)
            if lock_name:
                return lock_name

    def _send(self, message):
        self.request.send((message + '\n').encode())

    # FIXME: implement this
    # def get_action(self):
    #     pass


class TCPHandler(BaseTCPHandler):

    GLOBAL_LOCK = threading.Lock()
    """Global lock to serialize modification of LOCKS"""

    LOCKS = collections.defaultdict(Lock)
    """This dict contains the Lock instances"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock_name = None

    def _handle_lock(self, holder: Lock):
        try:
            try:
                self._real_handle_lock(holder)
            except utils.ClientDisconnected:
                logger.info("Client disconnected. Lock info: %s", holder)
        finally:
            holder.release()

    def _real_handle_lock(self, holder: Lock):
        """
        While control is in this method, the lock is held
        """
        self._send(RESPONSE_OK)
        binary_data = bytearray()
        while True:
            action = utils.try_get_line(self.request, binary_data, timeout=1.0)
            if action:
                logger.debug("Action: '%s' for lock %s", action, holder)
                binary_data = bytearray()
                if action == ACTION_RELEASE:
                    logger.info("Releasing lock: %s", holder)
                    self._send(RESPONSE_RELEASED)
                    self.request.close()
                    # FIXME: at this point we send OK to the client, but internally the lock is STILL HELD
                    return
                if action == ACTION_KEEPALIVE:
                    logger.debug("Received keepalive from client. Lock: %s", holder)
                    self._send(RESPONSE_STILL_ALIVE)
                else:
                    logger.warning("Unknown action '%s' for lock: %s", action, holder)

    def _handle_server_shutdown(self):
        # FIXME: assert connections came from localhost
        self._send(RESPONSE_SHUTTING_DOWN)  # FIXME: what if client had closed the socket?
        self.request.close()
        self.server.shutdown()

    def _handle_ping(self):
        self._send(RESPONSE_PONG)  # FIXME: what if client had closed the socket?
        self.request.close()

    def _handle_invalid_lock_hame(self, lock_name):
        logger.warning("Received invalid lock name: '%s'", lock_name)
        self._send(RESPONSE_ERR + ':invalid lock name')  # FIXME: what if client had closed the socket?
        self.request.close()

    def handle(self):
        try:
            line = self._get_line()
        except utils.ClientDisconnected:
            logger.info("Client disconnected before getting line.")
            self.request.close()
            return

        # FIXME: other exceptions we should handle here?

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
            self._handle_invalid_lock_hame(self._lock_name)
            return

        # Get the holder
        logger.debug('Trying to acquire GLOBAL_LOCK...')
        self.GLOBAL_LOCK.acquire()
        logger.debug('Got GLOBAL_LOCK')
        try:
            lock_holder = self.LOCKS[self._lock_name]
        finally:
            self.GLOBAL_LOCK.release()
            logger.debug('Released GLOBAL_LOCK')

        # Lock it
        granted = lock_holder.try_acquire(self._lock_name, client_id)
        if granted:
            logger.info("Lock acquired: %s", lock_holder)
            self._handle_lock(lock_holder)
        else:
            logger.info("Lock NOT acquired: %s", lock_holder)
            self._send(RESPONSE_LOCK_FAILED)  # FIXME: what if client had closed the socket?

        self.request.close()
