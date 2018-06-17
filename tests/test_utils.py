import threading
import time
import uuid

import pytest

from tcpnetlock.client import LockClient
from tcpnetlock.server import TCPServer


class ServerThread(threading.Thread):
    def __init__(self, initial_port=7654):
        super().__init__(daemon=True)
        server = None
        for port in range(initial_port, initial_port + 1000):
            try:
                server = TCPServer("localhost", port)
            except OSError as err:
                print("err.errno: {}".format(err.errno))
        assert server, "Could not bind server"
        self.server = server
        self.port = port

    def wait_for_server(self):
        """Busy-waits until the test server is responding"""
        connected = False
        lock_client = LockClient("localhost", self.port)
        for _ in range(50):
            try:
                lock_client.connect()
                connected = True
                break
            except ConnectionRefusedError:
                time.sleep(0.1)
        assert connected, "Couldn't connect to test server after many tries"
        lock_client.ping()
        lock_client.close()

    def get_client(self, **kwargs):
        """Returns a client instance to connect to test server"""
        host = kwargs.pop('host', 'localhost')
        port = kwargs.pop('port', self.port)
        return LockClient(host, port, **kwargs)

    def run(self):
        self.server.serve_forever()


@pytest.fixture(scope="module")
def lock_server() -> ServerThread:
    """
    Fixture, returns the server process running a TCPServer ready to use
    """

    server_thread = ServerThread()
    server_thread.start()
    server_thread.wait_for_server()

    yield server_thread

    client = server_thread.get_client()
    client.connect()
    client.server_shutdown()
    client.close()

    server_thread.join(5)
    assert not server_thread.is_alive(), "Server didn't shut down cleanly"


@pytest.fixture(scope="module")
def lock_name() -> str:
    return str(uuid.uuid4())
