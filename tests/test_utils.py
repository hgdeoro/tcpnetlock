import threading
import uuid

import pytest

from tcpnetlock.client import LockClient
from tcpnetlock.server import TCPServer


class ServerThread(threading.Thread):
    def __init__(self, port=0):
        super().__init__(daemon=True)
        self.server = TCPServer("localhost", port)
        self.port = self.server.port

    def get_client(self, **kwargs):
        """Returns a client instance to connect to test server"""
        host = kwargs.pop('host', 'localhost')
        port = kwargs.pop('port', self.port)
        return LockClient(host, port, **kwargs)

    def run(self):
        self.server.serve_forever()


@pytest.fixture
def lock_server() -> ServerThread:
    """
    Fixture, returns the server process running a TCPServer ready to use
    """

    server_thread = ServerThread()
    server_thread.start()

    yield server_thread

    client = server_thread.get_client()
    client.connect()
    client.server_shutdown()
    client.close()

    server_thread.join(1)
    assert not server_thread.is_alive(), "Server didn't shut down cleanly"


@pytest.fixture()
def lock_name() -> str:
    return str(uuid.uuid4())
