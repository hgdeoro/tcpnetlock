"""
Tests for `tcpnetlock.cli.tnl_client` package.
"""
import subprocess
import uuid

from tcpnetlock.cli import tnl_client
from tests.test_utils import ServerThread
from .test_utils import BaseTest
from .test_utils import lock_server, free_tcp_port, lock_name

assert lock_server
assert free_tcp_port
assert lock_name


class TestClientCli(BaseTest):

    def test_report_cant_connect(self, free_tcp_port):
        assert free_tcp_port > 0
        args = [
            'python', '-m', 'tcpnetlock.cli.tnl_client',
            '--debug',
            '--port={port}'.format(port=free_tcp_port),
               str(uuid.uuid4())
        ]
        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert completed_process.returncode == tnl_client.ERR_CONNECTION_REFUSED
        assert completed_process.stderr.decode().find('[Errno 111]') >= 0

    def test_cli_fails_lock_not_granted(self, lock_server: ServerThread, lock_name: str):
        lock_client = lock_server.get_client()
        lock_client.connect()
        assert lock_client.lock(lock_name)

        args = [
            'python', '-m', 'tcpnetlock.cli.tnl_client',
            '--debug',
            '--port={port}'.format(port=lock_server.port),
            lock_name
        ]
        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert completed_process.returncode == tnl_client.ERR_LOG_NOT_GRANTED
        assert completed_process.stderr.decode().find('not granted') >= 0
