import logging
import socket

import tcpnetlock.constants
from tcpnetlock import server
from tcpnetlock.common import Utils
from tcpnetlock.protocol import Protocol

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
        response_code = AcquireLockClientAction(
            self._protocol,
            None,
            [tcpnetlock.constants.RESPONSE_OK,
             tcpnetlock.constants.RESPONSE_LOCK_NOT_GRANTED,
             tcpnetlock.constants.RESPONSE_ERR]
        ).handle(lock_name=name, client_id=self._client_id)

        # FIXME: raise specific exception if RESPONSE_ERR is received (ex: InvalidClientId)
        return bool(response_code == tcpnetlock.constants.RESPONSE_OK)

    def server_shutdown(self):
        """Send order to shutdown the server"""
        return ClientAction(self._protocol,
                            tcpnetlock.constants.ACTION_SERVER_SHUTDOWN,
                            [tcpnetlock.constants.RESPONSE_SHUTTING_DOWN]).handle()

    def ping(self):
        """Send ping to the server"""
        return ClientAction(self._protocol,
                            tcpnetlock.constants.ACTION_PING,
                            [tcpnetlock.constants.RESPONSE_PONG]).handle()

    def keepalive(self):
        """Send a keepalive to the server"""
        return ClientAction(self._protocol,
                            tcpnetlock.constants.ACTION_KEEPALIVE,
                            [tcpnetlock.constants.RESPONSE_STILL_ALIVE]).handle()

    def release(self):
        """Release the held lock"""
        return ClientAction(self._protocol,
                            tcpnetlock.constants.ACTION_RELEASE,
                            [tcpnetlock.constants.RESPONSE_RELEASED]).handle()

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


class ClientAction:

    GENERATE_CUSTOM_MESSAGE = False

    def __init__(self, protocol: Protocol, message: str, valid_responses: list):
        self.protocol = protocol
        self.message = message
        self.valid_responses = valid_responses

        assert self.protocol
        assert self.message or self.GENERATE_CUSTOM_MESSAGE
        assert len(self.valid_responses)

    def parse_and_validate_response(self, line: str):
        response_code, *ignored = line.split(",", maxsplit=1)
        assert response_code in self.valid_responses,\
            "Invalid response: '{response_code}'. Valid responses: {valid_response_codes}. Full line: {line}".format(
                response_code=response_code,
                valid_response_codes=self.valid_responses,
                line=line
            )
        return response_code

    def read_valid_response(self):
        line = self.protocol.readline()
        response_code = self.parse_and_validate_response(line)
        return response_code

    def get_message(self, **kwargs):
        return self.message

    def handle(self, **kwargs):
        message = self.get_message(**kwargs)
        logger.debug("Sending message to server: %s", message)
        self.protocol.send(message)
        return self.read_valid_response()


class AcquireLockClientAction(ClientAction):

    GENERATE_CUSTOM_MESSAGE = True

    def get_message(self, lock_name, **kwargs):
        client_id = kwargs.pop('client_id')
        message = "lock,name:{lock_name}".format(lock_name=lock_name)
        if client_id:
            message += ",client-id:{client_id}".format(client_id=client_id)
        return message
