import collections
import logging
import socketserver
import threading
import time

from tcpnetlock import constants as const
from tcpnetlock.protocol import Protocol
from tcpnetlock.server import action_handlers as handlers
from tcpnetlock.server.action import Action
from tcpnetlock.common import ClientDisconnected

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
        b. if lock was NOT granted, returns 'not-granted\n' to the client and the TCP connection is immediately CLOSED
"""

logger = logging.getLogger(__name__)


class Lock:

    def __init__(self):
        self._lock = threading.Lock()
        self._name = None
        self._timestamp = 0
        self._client_id = None

    def acquire_non_blocking(self):
        return self._lock.acquire(blocking=False)

    def update(self, lock_name, client_id):
        if self._name is None:
            self._name = lock_name
        else:
            assert self._name == lock_name

        self._timestamp = time.time()
        self._client_id = client_id

    def release(self):
        self._lock.release()

    def __str__(self):
        return "Lock '{name}', client '{client}', age: {age}".format(
            name=self._name, client=self._client_id, age=int(time.time() - self._timestamp))


class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    DEFAULT_PORT = 7654

    def __init__(self, host='localhost', port=DEFAULT_PORT):
        super().__init__((host, port), TCPHandler)

    @property
    def port(self):
        return self.socket.getsockname()[1]


class TCPHandler(socketserver.BaseRequestHandler):

    GLOBAL_LOCK = threading.Lock()
    """Global lock to serialize modification of LOCKS"""

    LOCKS = collections.defaultdict(Lock)
    """This dict contains the Lock instances"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _invalid_request(self, protocol: Protocol, line: str):
        logger.warning("Received invalid request: '%s'", line)
        protocol.send(const.RESPONSE_INVALID_REQUEST)
        self.request.close()

    def handle(self):
        protocol = Protocol(self.request)
        try:
            line = protocol.readline()
        except ClientDisconnected:
            logger.info("Client disconnected before getting line.")
            protocol.close()
            return

        action = Action.from_line(line)
        if action.is_valid():
            logger.debug("Received valid action: '%s'", action)
        else:
            return self._invalid_request(protocol, line)

        if action.name == const.ACTION_SERVER_SHUTDOWN:
            return handlers.ShutdownActionHandler(protocol, action, server=self.server).handle_action()

        if action.name == const.ACTION_PING:
            return handlers.PingActionHandler(protocol, action).handle_action()

        if action.name != const.ACTION_LOCK:
            return handlers.InvalidActionActionHandler(protocol, action).handle_action()

        lock_name = action.params.get('name')
        if not const.VALID_LOCK_NAME_RE.match(lock_name):
            return handlers.InvalidLockActionHandler(protocol, action, lock_name=lock_name).handle_action()

        # Get the Lock, only while holding the GLOBAL LOCK
        # This is done to avoid 2 concurrent clients creating 2 instances of the same lock at the same time
        with self.GLOBAL_LOCK:
            lock = self.LOCKS[lock_name]

        # Acquire lock and proceed, or return failure.
        # If multiple concurrent clients try to get the lock, only one will proceed
        if lock.acquire_non_blocking():
            try:
                return handlers.LockGrantedActionHandler(
                    protocol, action, lock=lock, lock_name=lock_name).handle_action()
            finally:
                lock.release()
        else:
            return handlers.LockNotGrantedActionHandler(protocol, action, lock_name=lock_name).handle_action()
