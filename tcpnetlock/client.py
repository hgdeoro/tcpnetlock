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

    def connect(self):
        self.socket.connect(("localhost", 9999))

    def lock(self, name):
        self.socket.send(f"{name}\n".encode())
        logger.info(f"Acquiring lock '{name}'")
        response = utils.get_line(self.socket)
        assert response in ("ok", "err"), f"Invalid response: '{response}'"
        return response == "ok"

    def server_shutdown(self):
        self.socket.send(f"{server.SERVER_SHUTDOWN}\n".encode())
        response = utils.get_line(self.socket)
        assert response == "shutting-down", response
        logger.info("Shutdown sent to server")
        return response

    def ping(self):
        self.socket.send(f"{server.PING}\n".encode())
        response = utils.get_line(self.socket)
        assert response == "pong"
        logger.info("Ping OK")
        return response

    def close(self):
        self.socket.close()


LockClient = _TemporalLockClient
