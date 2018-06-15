import logging
import socket
import re

from tcpnetlock import server
from tcpnetlock import utils

logger = logging.getLogger(__name__)


VALID_LOCK_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


class _TemporalLockClient:
    """
    This is a temporal implementation of the client, with just the basic stuff to be able to develop
    unittests for the server code. Some of this code may be used, in the future, for the implementation
    of the real client.
    """

    def __init__(self, host='localhost', port=9999):
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._acquired = None

    @staticmethod
    def valid_lock_name(lock_name):
        """Returns True if the provided lock name is valid"""
        return bool(VALID_LOCK_NAME_RE.match(lock_name))

    @staticmethod
    def _assert_response(response, valid_responses):
        assert response in valid_responses, f"Invalid response: '{response}'. Valid responses: {valid_responses}"

    def _send(self, message):
        self._socket.send((message + '\n').encode())

    def _read_response(self, valid_responses):
        response = utils.get_line(self._socket)
        self._assert_response(response, valid_responses)
        return response

    def connect(self):
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
        response = self._read_response([server.RESPONSE_OK])
        acquired = (response == server.RESPONSE_OK)
        logging.info("Lock %s acquired: %s", name, acquired)
        return acquired

    def server_shutdown(self):
        logger.info("Sending SHUTDOWN...")
        self._send(server.ACTION_SERVER_SHUTDOWN)
        return self._read_response([server.RESPONSE_SHUTTING_DOWN])

    def ping(self):
        logger.info("Sending PING...")
        self._send(server.ACTION_PING)
        return self._read_response([server.RESPONSE_PONG])

    def release(self):
        logger.info("Trying to RELEASE...")
        self._send(server.ACTION_RELEASE)
        return self._read_response([server.RESPONSE_RELEASED])

    def close(self):
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
