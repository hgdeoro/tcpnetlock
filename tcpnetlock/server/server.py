import collections
import logging
import socketserver
import threading
import time

from tcpnetlock import constants as const
from tcpnetlock.common import Counter
from tcpnetlock.common import ClientDisconnected
from tcpnetlock.protocol import Protocol
from tcpnetlock.server import action_handlers as handlers
from tcpnetlock.server.action import Action

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

# FIXME: this module has too much code, we need to refactor, specially Context, should be an instance not a class

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

        self._timestamp = time.monotonic()
        self._client_id = client_id

    @property
    def locked(self):
        return self._lock.locked()

    def release(self):
        self._lock.release()

    @property
    def age(self):
        return time.monotonic() - self._timestamp

    def __str__(self):
        return "Lock: '{name}', client-id: '{client}', age: {age}".format(
            name=self._name, client=self._client_id or '', age=int(self.age))


class Context:

    GLOBAL_LOCK = threading.Lock()
    """Global lock to serialize modification of LOCKS"""

    LOCKS = collections.defaultdict(Lock)
    """This dict contains the Lock instances"""

    REQUESTS_COUNT = Counter()
    """How many requests were accepted"""

    LOCK_ACKQUIRED_COUNT = Counter()
    """How many times a lock was acquired"""

    LOCK_NOT_ACKQUIRED_COUNT = Counter()
    """How many times a lock was NOT acquired"""

    @classmethod
    def counters(cls):
        return {
            'request_count': cls.REQUESTS_COUNT.count,
            'lock_acquired_count': cls.LOCK_ACKQUIRED_COUNT.count,
            'lock_not_acquired_count': cls.LOCK_NOT_ACKQUIRED_COUNT.count,
        }


class BackgrounThread(threading.Thread):
    daemon = True
    iteration_wait = 5
    min_age = 5
    logger = logging.getLogger("{}.BackgrounThread".format(__name__))

    def run(self):
        while True:
            self.logger.info("Running cleanup")
            for key in self._get_keys():
                try:
                    self._check_key(key)
                except:  # noqa: E722 we need to ignore any error
                    self.logger.exception("Exception detected in BackgrounThread while checking key '%s'", key)
            time.sleep(self.iteration_wait)

    def _get_keys(self):
        try:
            # May raise 'RuntimeError: dictionary changed size during iteration'
            return list(Context.LOCKS.keys())
        except RuntimeError:
            self.logger.info("RuntimeError detected when trying to get list of keys. "
                             "Will retry holding GLOBAL_LOCK", exc_info=True)
            with Context.GLOBAL_LOCK:
                return list(Context.LOCKS.keys())

    def _check_key(self, key):
        lock = Context.LOCKS[key]
        if lock.locked:
            return
        if lock.age < self.min_age:
            return

        ackquired = False
        try:
            ackquired = lock.acquire_non_blocking()
            if not ackquired:
                self.logger.info("Weird... couldn't get the lock to delete '%s'", key)
                return

            # We got the lock, we can remove it from the dict
            self.logger.info("Cleaning key '%s'", key)
            del Context.LOCKS[key]

        finally:
            if ackquired:
                lock.release()


class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    DEFAULT_PORT = 7654

    def __init__(self, host='localhost', port=DEFAULT_PORT):
        super().__init__((host, port), TCPHandler)
        self._background_thread = BackgrounThread()

    @property
    def port(self):
        return self.socket.getsockname()[1]

    def serve_forever(self, *args, **kwargs):
        self._background_thread.start()
        super().serve_forever(*args, **kwargs)


class TCPHandler(socketserver.BaseRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _invalid_request(self, protocol: Protocol, line: str):
        logger.warning("Received invalid request: '%s'", line)
        protocol.send(const.RESPONSE_INVALID_REQUEST)
        self.request.close()

    def handle(self):
        Context.REQUESTS_COUNT.incr()
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

        if action.name == const.ACTION_STATS:
            return handlers.StatsActionHandler(protocol, action, context=Context).handle_action()

        if action.name != const.ACTION_LOCK:
            return handlers.InvalidActionActionHandler(protocol, action).handle_action()

        lock_name = action.params.get('name')
        if not const.VALID_LOCK_NAME_RE.match(lock_name):
            return handlers.InvalidLockActionHandler(protocol, action, lock_name=lock_name).handle_action()

        # Get the Lock, only while holding the GLOBAL LOCK
        # This is done to avoid 2 concurrent clients creating 2 instances of the same lock at the same time
        with Context.GLOBAL_LOCK:
            lock = Context.LOCKS[lock_name]

        # Acquire lock and proceed, or return failure.
        # If multiple concurrent clients try to get the lock, only one will proceed
        if lock.acquire_non_blocking():
            Context.LOCK_ACKQUIRED_COUNT.incr()
            try:
                return handlers.LockGrantedActionHandler(
                    protocol, action, lock=lock, lock_name=lock_name).handle_action()
            finally:
                lock.release()
        else:
            Context.LOCK_NOT_ACKQUIRED_COUNT.incr()
            return handlers.LockNotGrantedActionHandler(protocol, action, lock_name=lock_name).handle_action()
