"""
Tests for `tcpnetlock.client` and `tcpnetlock.server` packages.
"""
import subprocess

from tcpnetlock.cli import tnl_server
from .test_utils import BaseTest
from .test_utils import ServerThread
from .test_utils import lock_server

assert lock_server


class TestServerCli(BaseTest):
    def test_report_bind_to_used_port(self, lock_server: ServerThread):
        args = [
            'python', '-m', 'tcpnetlock.cli.tnl_server',
            '--port={port}'.format(port=lock_server.port),
        ]
        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert completed_process.returncode == tnl_server.ERR_SERVER_BIND
        assert completed_process.stderr.decode().find('[Errno 98]') >= 0

    def test_report_bind_to_privileged_port(self, lock_server: ServerThread):
        args = [
            'python', '-m', 'tcpnetlock.cli.tnl_server',
            '--port=20',
        ]
        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert completed_process.returncode == tnl_server.ERR_SERVER_BIND
        assert completed_process.stderr.decode().find('[Errno 13]') >= 0
