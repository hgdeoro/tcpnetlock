import logging
import socket

from tcpnetlock import common
from tcpnetlock import constants
from tcpnetlock.client.action import AcquireLockClientAction
from tcpnetlock.client.action import ClientAction
from tcpnetlock.common import Utils
from tcpnetlock.protocol import Protocol
from tcpnetlock.server import server

logger = logging.getLogger(__name__)


class LockClient:
    DEFAULT_PORT = server.TCPServer.DEFAULT_PORT

    def __init__(self, host='localhost', port=DEFAULT_PORT, client_id=None):
        """
        Creates a client to connect to the server.

        :param host: hostname of the server
        :param port: port to connect
        """
        self._host = host
        self._port = port
        self._acquired = None
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._protocol = Protocol(self._socket)
        self._client_id = client_id
        Utils.validate_client_id(client_id)

    def connect(self):
        """
        Connects to server.

        :raises ConnectionRefusedError if connection is refused
        :return:
        """
        logger.info("Connecting to '%s:%s'...", self._host, self._port)
        self._socket.connect((self._host, self._port))

    def lock(self, name: str) -> bool:
        """
        Tries to acquire a lock

        :param name: lock name
        :return: boolean indicating if lock as acquired or not
        """
        if not Utils.valid_lock_name(name):
            raise common.InvalidLockNameError("Lock name is invalid: '{lock_name}'".format(lock_name=name))

        response_code = AcquireLockClientAction(
            self._protocol,
            None,
            [constants.RESPONSE_OK,
             constants.RESPONSE_LOCK_NOT_GRANTED,
             constants.RESPONSE_ERR]
        ).handle(lock_name=name, client_id=self._client_id)

        # FIXME: raise specific exception if RESPONSE_ERR is received (ex: InvalidClientId)
        self._acquired = bool(response_code == constants.RESPONSE_OK)
        return self._acquired

    def server_shutdown(self):
        """Send order to shutdown the server"""
        return ClientAction(self._protocol,
                            constants.ACTION_SERVER_SHUTDOWN,
                            [constants.RESPONSE_SHUTTING_DOWN]).handle()

    def ping(self):
        """Send ping to the server"""
        return ClientAction(self._protocol,
                            constants.ACTION_PING,
                            [constants.RESPONSE_PONG]).handle()

    def keepalive(self):
        """Send a keepalive to the server"""
        return ClientAction(self._protocol,
                            constants.ACTION_KEEPALIVE,
                            [constants.RESPONSE_STILL_ALIVE]).handle()

    def release(self):
        """Release the held lock"""
        return ClientAction(self._protocol,
                            constants.ACTION_RELEASE,
                            [constants.RESPONSE_RELEASED]).handle()

    def close(self):
        """Close the socket. As a result of the disconnection, the lock will be released at the server."""
        logger.debug("Closing the socket...")
        self._protocol.close()

    @property
    def acquired(self) -> bool:
        """
        Returns boolean indicating if lock was acquired or not
        :return: True if lock was acquired, False otherwise
        """
        assert self._acquired in (True, False)  # Fail if lock() wasn't called
        return self._acquired
