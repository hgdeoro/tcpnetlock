import threading
import time

import pytest

from tcpnetlock.client import LockClient
from tcpnetlock.server import LockServer


def _wait_for_server():
    """
    Busy-waits until the test server is responding
    """
    client = LockClient()
    for _ in range(10):
        try:
            client.connect()
            break
        except ConnectionRefusedError:
            time.sleep(0.1)
    client.ping()
    client.close()


@pytest.fixture(scope="module")
def lock_server():
    """
    Fixture, returns the server process running a LockServer ready to use
    """
    def start_server():
        # FIXME: get a random port
        server = LockServer("localhost", 9999)
        server.serve_forever()

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    _wait_for_server()  # wait until server is ready

    yield server_thread

    client = LockClient()
    client.connect()
    client.server_shutdown()
    client.close()

    server_thread.join(5)
    assert not server_thread.is_alive(), "Server didn't shut down cleanly"
