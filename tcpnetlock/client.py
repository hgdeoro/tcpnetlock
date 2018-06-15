import logging
import socket

from tcpnetlock import server
from tcpnetlock import utils

logger = logging.getLogger(__name__)


class _TemporalLockClient:
    """
    This is a temporal implementation of the client, with just the basic stuff to be able to develop
    unittests for the server code. Some of this code may be used, in the future, for the implementation
    of the real client.
    """

    def __init__(self, host='localhost', port=9999):
        """
        Creates a client to connect to the server.

        :param host: hostname of the server
        :param port: port to connect
        """
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._acquired = None

    @staticmethod
    def valid_lock_name(lock_name):
        """Returns True if the provided lock name is valid"""
        return bool(server.VALID_LOCK_NAME_RE.match(lock_name))

    @staticmethod
    def _assert_response(response: str, valid_response_codes):
        response_code = response.split(":")[0]
        assert response_code in valid_response_codes,\
            f"Invalid response: '{response}'. Valid responses: {valid_response_codes}"

    def _send(self, message):
        self._socket.send((message + '\n').encode())

    def _read_response(self, valid_responses):
        response = utils.get_line(self._socket)
        self._assert_response(response, valid_responses)
        return response

    def connect(self):
        """Connects to the server"""
        logger.info("Connecting to '%s:%s'...", self._host, self._port)
        self._socket.connect((self._host, self._port))

    def lock(self, name: str) -> bool:
        """
        Tries to acquire a lock
        :param name: lock name
        :return: boolean indicating if lock as acquired or not
        """
        assert self.valid_lock_name(name)
        logger.info("Trying to acquire lock '%s'...", name)
        self._send(name)
        response = self._read_response([server.RESPONSE_OK, server.RESPONSE_LOCK_FAILED, server.RESPONSE_ERR])
        self._acquired = (response == server.RESPONSE_OK)
        logging.info("Lock %s acquired: %s", name, self._acquired)
        return self._acquired

    def server_shutdown(self):
        """Send order to shutdown the server"""
        logger.info("Sending SHUTDOWN...")
        self._send(server.ACTION_SERVER_SHUTDOWN)
        return self._read_response([server.RESPONSE_SHUTTING_DOWN])

    def ping(self):
        """Send ping to the server"""
        logger.info("Sending PING...")
        self._send(server.ACTION_PING)
        return self._read_response([server.RESPONSE_PONG])

    def release(self):
        """Release the held lock"""
        logger.info("Trying to RELEASE...")
        self._send(server.ACTION_RELEASE)
        return self._read_response([server.RESPONSE_RELEASED])

    def close(self):
        """Close the socket. As a result of the disconnection, the lock will be released at the server."""
        self._socket.close()

    @property
    def acquired(self) -> bool:
        """
        Returns boolean indicating if lock was acquired or not
        :return: True if lock was acquired, False otherwise
        """
        assert self._acquired in (True, False)  # Fail if lock() wasn't called
        return self._acquired


LockClient = _TemporalLockClient
