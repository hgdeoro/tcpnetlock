import logging
import socket

from tcpnetlock.constants import NEW_LINE_BINARY
from tcpnetlock.common import ClientDisconnected

logger = logging.getLogger(__name__)


class Protocol:
    """
    Encapsulates the read/write operations on the socket for the string, line-oriented protocol used
    by the server and client.
    """
    # FIXME: control length of line

    def __init__(self, sock: socket.socket):
        self.socket = sock
        self.buffer = bytearray()

    def close(self):
        logger.debug("socket.close()")
        self.socket.close()

    def send(self, message):
        logger.debug("socket.sendall('%s')", message)
        self.socket.sendall((message + '\n').encode())

    def _line_in_buffer(self):
        return self.buffer.find(NEW_LINE_BINARY) >= 0

    def _get_line_from_buffer(self) -> str:
        assert self._line_in_buffer()
        head, tail = self.buffer.split(NEW_LINE_BINARY, 1)
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

    def check_connection(self):
        """
        Raises ClientDisconnected if connection is closed (this is used to detect cases like if the server died.
        """
        # FIXME: must be a better way to implement this check :/
        self.socket.settimeout(1)
        try:
            recv_data = self.socket.recv(1)
        except socket.timeout:
            return  # this is not a guaranty that TCP connection still exists

        if recv_data:
            self.buffer.extend(recv_data)
        else:
            raise ClientDisconnected()
