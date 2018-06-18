import collections
import logging
import socket
import socketserver
import threading
import time

from tcpnetlock.constants import RESPONSE_ERR, RESPONSE_INVALID_REQUEST, RESPONSE_LOCK_NOT_GRANTED, RESPONSE_RELEASED, \
    RESPONSE_SHUTTING_DOWN, RESPONSE_PONG, RESPONSE_STILL_ALIVE, ACTION_RELEASE, ACTION_SERVER_SHUTDOWN, ACTION_PING, \
    ACTION_KEEPALIVE, VALID_LOCK_NAME_RE, RESPONSE_OK
from tcpnetlock.utils import ClientDisconnected
from tcpnetlock.utils import ignore_client_disconnected_exception

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

NEW_LINE = '\n'.encode()


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


class Action:

    def __init__(self, action: str, params: dict):
        self.action = action
        self.params = params

    @property
    def name(self):
        return self.action

    def is_valid(self):
        # action, and param keys must be non-empty
        return \
            len(self.action) > 0 \
            and all(len(p) > 0 for p in self.params.keys())

    @classmethod
    def from_line(cls, line: str):
        action, *raw_params = line.split(',')
        params = []
        for key, *values in [p.split(':', 1) for p in raw_params]:
            if values:
                assert len(values) == 1
                param = [key.strip(), values[0].strip()]
            else:
                param = [key.strip(), '']
            params.append(param)
        return Action(action.strip(), dict(params))


class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    DEFAULT_PORT = 7654

    def __init__(self, host='localhost', port=DEFAULT_PORT):
        super().__init__((host, port), TCPHandler)


class Protocol:
    # FIXME: control length of line

    def __init__(self, sock: socket.socket):
        self.socket = sock
        self.buffer = bytearray()

    def _send(self, message):
        # FIXME: REMOVE THIS METHOD
        logger.debug("sendall('%s')", message)
        self.socket.sendall((message + '\n').encode())

    def close(self):
        logger.debug("socket.close()")
        self.socket.close()

    def send(self, message):
        logger.debug("socket.sendall('%s')", message)
        self.socket.sendall((message + '\n').encode())

    def _line_in_buffer(self):
        return self.buffer.find(NEW_LINE) >= 0

    def _get_line_from_buffer(self) -> str:
        assert self._line_in_buffer()
        head, tail = self.buffer.split(NEW_LINE, 1)
        self.buffer = tail
        return head.decode()

    def _readline_blocking(self) -> str:
        """Returns line, or raises ClientDisconnected if socket is closed"""
        logger.debug('Disabling socket timeout (will block)')
        self.socket.settimeout(None)
        while True:
            logger.debug('Reading from socket')
            recv_data = self.socket.recv(128)
            if not recv_data:
                raise ClientDisconnected()
            self.buffer.extend(recv_data)
            if self._line_in_buffer():
                return self._get_line_from_buffer()

    def _readline_non_blocking(self, timeout: int) -> str:
        """Wait for up to `timeout` for a line"""
        # FIXME: this implementation will wait AT LEAST `timeout`, but maybe more than that
        logger.debug('Setting socket timeout to %s', timeout)
        self.socket.settimeout(timeout)
        while True:
            if self._line_in_buffer():
                return self._get_line_from_buffer()
            try:
                logger.debug('Reading from socket')
                recv_data = self.socket.recv(128)
                if recv_data:
                    self.buffer.extend(recv_data)
                else:
                    raise ClientDisconnected()
            except socket.timeout:
                logger.debug('Reading from socket TIMED OUT')
                return None

    def readline(self, timeout=None) -> str:
        """
        Reads socket and returns a line.

        If partial data is received, but not an entire line, then None is returned.

        :return: line or None
        """

        if self._line_in_buffer():
            return self._get_line_from_buffer()

        if timeout is None:
            return self._readline_blocking()
        else:
            return self._readline_non_blocking(timeout=timeout)


class TCPHandler(socketserver.BaseRequestHandler):

    GLOBAL_LOCK = threading.Lock()
    """Global lock to serialize modification of LOCKS"""

    LOCKS = collections.defaultdict(Lock)
    """This dict contains the Lock instances"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _invalid_request(self, protocol: Protocol, line: str):
        logger.warning("Received invalid request: '%s'", line)
        protocol.send(RESPONSE_INVALID_REQUEST)
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

        if line == ACTION_SERVER_SHUTDOWN:
            return ShutdownActionHandler(protocol, action, server=self.server).handle_action()

        if line == ACTION_PING:
            return PingActionHandler(protocol, action).handle_action()

        if not VALID_LOCK_NAME_RE.match(action.action):
            return InvalidLockActionHandler(protocol, action).handle_action()

        # Get the Lock, only while holding the GLOBAL LOCK
        with self.GLOBAL_LOCK:
            lock = self.LOCKS[action.name]

        # Acquire lock and proceed, or return failure
        if lock.acquire_non_blocking():
            try:
                return LockGrantedActionHandler(protocol, action, lock=lock).handle_action()
            finally:
                lock.release()
        else:
            return LockNotGrantedActionHandler(protocol, action).handle_action()


class ActionHandler:
    def __init__(self, protocol: Protocol, action: Action):
        self.protocol = protocol
        self.action = action


class ShutdownActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.server = kwargs.pop('server')
        super().__init__(*args, **kwargs)

    def can_proceed(self):
        # FIXME: assert connections came from localhost
        return True

    def handle_action(self):
        if not self.can_proceed():
            pass  # FIXME: do something
        self.protocol.send(RESPONSE_SHUTTING_DOWN)
        self.protocol.close()
        self.server.shutdown()


class PingActionHandler(ActionHandler):

    def handle_action(self):
        self.protocol.send(RESPONSE_PONG)
        self.protocol.close()


class InvalidLockActionHandler(ActionHandler):

    def handle_action(self):
        logger.warning("Received invalid lock name: '%s'", self.action.action)
        self.protocol.send(RESPONSE_ERR + ':invalid lock name')
        self.protocol.close()


class LockNotGrantedActionHandler(ActionHandler):

    def handle_action(self):
        logger.info("Lock NOT granted: %s", self.action.action)
        self.protocol.send(RESPONSE_LOCK_NOT_GRANTED)
        self.protocol.close()


class LockGrantedActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        super().__init__(*args, **kwargs)

    @ignore_client_disconnected_exception
    def handle_action(self):
        self.lock.update(self.action.name, self.action.params.get('client-id'))
        self.protocol.send(RESPONSE_OK)

        while True:
            line = self.protocol.readline(timeout=1.0)
            if line is None:
                continue

            inner_action = Action.from_line(line)
            logger.debug("Inner action: '%s' for lock %s", inner_action, self.lock)

            if inner_action.name == ACTION_RELEASE:
                return InnerReleaseLockActionHandler(self.protocol, inner_action, lock=self.lock).handle_action()
            if inner_action.name == ACTION_KEEPALIVE:
                InnerKeepAliveActionHandler(self.protocol, inner_action, lock=self.lock).handle_action()
            else:
                logger.warning("Ignoring unknown action '%s' for lock: %s", inner_action.name, self.lock)


class InnerReleaseLockActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        super().__init__(*args, **kwargs)

    def handle_action(self):
        logger.info("Releasing lock: %s", self.lock)
        self.protocol.send(RESPONSE_RELEASED)
        self.protocol.close()


class InnerKeepAliveActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        super().__init__(*args, **kwargs)

    def handle_action(self):
        logger.debug("Received keepalive from client. Lock: %s", self.lock)
        self.protocol.send(RESPONSE_STILL_ALIVE)
