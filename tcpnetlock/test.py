import logging
import multiprocessing
import time
import unittest

from tcpnetlock.client import LockClient
from tcpnetlock.server import LockServer


class ServerTestCase(unittest.TestCase):

    def _wait_for_server(self):
        client = LockClient()
        for _ in range(10):
            try:
                client.connect()
                break
            except ConnectionRefusedError:
                time.sleep(0.1)

        client.ping()
        client.close()

    def setUp(self):
        def start_server():
            server = LockServer("localhost", 9999)
            server.serve_forever()

        self.process = multiprocessing.Process(target=start_server)
        self.process.daemon = True
        self.process.start()

        # wait until server is ready
        self._wait_for_server()

    def tearDown(self):
        client = LockClient()
        client.connect()
        client.server_shutdown()
        client.close()

        self.process.join(1)
        self.process.terminate()

    def test_connect_and_get_lock_works(self):
        client = LockClient()
        client.connect()
        acquired = client.lock('lock1')
        self.assertTrue(acquired)
        client.close()

    def test_get_two_different_lock(self):
        client = LockClient()
        client.connect()
        acquired = client.lock('lock1')
        self.assertTrue(acquired)
        client.close()

        client2 = LockClient()
        client2.connect()
        acquired = client2.lock('lock2')
        self.assertTrue(acquired)
        client2.close()

    def test_lock_twice(self):
        client1 = LockClient()
        client1.connect()
        acquired = client1.lock('lock1')
        self.assertTrue(acquired)

        client2 = LockClient()
        client2.connect()
        acquired = client2.lock('lock1')
        self.assertFalse(acquired)

        client1.close()
        client2.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
