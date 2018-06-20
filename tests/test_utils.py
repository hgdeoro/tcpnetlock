import threading
import time
import uuid

import pytest

from tcpnetlock.client.client import LockClient
from tcpnetlock.server.server import TCPServer


class BaseTest:

    def get_client_with_lock_acquired(self, lock_server, name, repeat=20, wait=0.3) -> LockClient:
        """
        Loop until we can get the lock. This is needed because the way the server works when RELEASING a lock:
        it first respond 'ok', and then it release the real lock... If a test case release the lock and then tries
        to re-ackquire it, the server might fail, so in this case we should retry a few more times.
        """
        iters = list(range(repeat))
        while iters:
            iters.pop()
            client = lock_server.get_client()
            client.connect()
            acquired = client.lock(name)
            if acquired:
                return client
            client.close()
            if iters:
                time.sleep(wait)

        return None


class ServerThread(threading.Thread):
    """
    Thread impl to run the server in a subthread
    """
    def __init__(self, port=0):
        super().__init__(daemon=True)
        self.server = TCPServer("localhost", port)
        self.port = self.server.port

    def get_client(self, **kwargs) -> LockClient:
        """Returns a client instance to connect to test server"""
        host = kwargs.pop('host', 'localhost')
        port = kwargs.pop('port', self.port)
        return LockClient(host, port, **kwargs)

    def run(self):
        self.server.serve_forever()


@pytest.fixture(scope='module')
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
