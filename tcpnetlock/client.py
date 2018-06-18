import logging
import socket

import tcpnetlock.constants
from tcpnetlock import server
from tcpnetlock import utils

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
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._acquired = None
        if client_id:
            assert self.valid_client_id(client_id), "Invalid client_id: {client_id}".format(client_id=client_id)
        self._client_id = client_id

    @staticmethod
    def valid_lock_name(lock_name):
        """Returns True if the provided lock name is valid"""
        return bool(tcpnetlock.constants.VALID_LOCK_NAME_RE.match(lock_name))

    @staticmethod
    def valid_client_id(client_id):
        """Returns True if the provided client_id is valid"""
        return bool(tcpnetlock.constants.VALID_CLIENT_ID_RE.match(client_id))

    @staticmethod
    def _assert_response(response: str, valid_response_codes):
        response_code = response.split(":")[0]
        assert response_code in valid_response_codes,\
            "Invalid response: '{response}'. Valid responses: {valid_response_codes}".format(
                response=response, valid_response_codes=valid_response_codes
            )

    def _send(self, message: str):
        assert message
        self._socket.send((message + '\n').encode())

    def _read_response(self, valid_responses):
        # FIXME: we should time-out here after some time
        response = utils.get_line(self._socket)
        self._assert_response(response, valid_responses)
        return response

    def connect(self):
        """Connects to the server"""
        logger.info("Connecting to '%s:%s'...", self._host, self._port)
        try:
            self._socket.connect((self._host, self._port))
        except ConnectionRefusedError:
            raise

    def lock(self, name: str) -> bool:
        """
        Tries to acquire a lock
        :param name: lock name
        :return: boolean indicating if lock as acquired or not
        """
        assert self.valid_lock_name(name)
        logger.info("Trying to acquire lock '%s'...", name)
        if self._client_id:
            message = "{name},client-id:{client_id}".format(name=name, client_id=self._client_id)
        else:
            message = name
        self._send(message)
        response = self._read_response([tcpnetlock.constants.RESPONSE_OK,
                                        tcpnetlock.constants.RESPONSE_LOCK_NOT_GRANTED,
                                        tcpnetlock.constants.RESPONSE_ERR])
        self._acquired = (response == tcpnetlock.constants.RESPONSE_OK)
        logging.info("Lock %s acquired: %s", name, self._acquired)

        return self._acquired

    def server_shutdown(self):
        """Send order to shutdown the server"""
        logger.info("Sending SHUTDOWN...")
        self._send(tcpnetlock.constants.ACTION_SERVER_SHUTDOWN)
        return self._read_response([tcpnetlock.constants.RESPONSE_SHUTTING_DOWN])

    def ping(self):
        """Send ping to the server"""
        logger.info("Sending PING...")
        self._send(tcpnetlock.constants.ACTION_PING)
        return self._read_response([tcpnetlock.constants.RESPONSE_PONG])

    def keepalive(self):
        """Send a keepalive to the server"""
        logger.info("Sending KEEPALIVE...")
        self._send(tcpnetlock.constants.ACTION_KEEPALIVE)
        response = self._read_response([tcpnetlock.constants.RESPONSE_STILL_ALIVE])
        return response

    def release(self):
        """Release the held lock"""
        logger.info("Trying to RELEASE...")
        self._send(tcpnetlock.constants.ACTION_RELEASE)
        return self._read_response([tcpnetlock.constants.RESPONSE_RELEASED])

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
