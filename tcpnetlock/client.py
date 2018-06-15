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

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _send(self, message):
        self.socket.send((message + '\n').encode())

    def connect(self):
        self.socket.connect(("localhost", 9999))

    def lock(self, name):
        logger.info("Trying to acquire lock '%s'", name)
        self._send(name)
        response = utils.get_line(self.socket)
        assert response in (server.RESPONSE_OK, server.RESPONSE_ERR), f"Invalid response: '{response}'"
        return response == server.RESPONSE_OK

    def server_shutdown(self):
        self._send(server.ACTION_SERVER_SHUTDOWN)
        logger.info("Shutdown sent to server")
        response = utils.get_line(self.socket)
        assert response == server.RESPONSE_SHUTTING_DOWN, response
        return response

    def ping(self):
        self._send(server.ACTION_PING)
        logger.info("Ping sent to server")
        response = utils.get_line(self.socket)
        assert response == server.RESPONSE_PONG
        return response

    def release(self):
        self._send(server.ACTION_RELEASE)
        response = utils.get_line(self.socket)
        assert response == server.RESPONSE_RELEASED
        logger.info("Released")
        return response

    def close(self):
        self.socket.close()


LockClient = _TemporalLockClient
