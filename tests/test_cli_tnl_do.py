"""
Tests for `tcpnetlock.cli.tnl_do` package.
"""

import re
import subprocess

import pytest

from tcpnetlock.cli import tnl_do
from tcpnetlock.client.client import LockClient

from .test_utils import ServerThread
from .test_utils import lock_server
from .test_utils import lock_name
from .test_utils import free_tcp_port

assert lock_server
assert lock_name
assert free_tcp_port


class TestRunWithLock:

    def _run(self, lock_name, lock_server, *args) -> subprocess.CompletedProcess:
        port_arg = [arg for arg in args if arg.startswith('--port=')] or ['--port={port}'.format(port=lock_server.port)]
        base_args = [
            'python', '-m', 'tcpnetlock.cli.tnl_do',
            '--host=localhost',
            '--lock-name={lock_name}'.format(lock_name=lock_name),
        ] + port_arg

        full_args = base_args + list(args)

        completed_process = subprocess.run(full_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return completed_process

    def test_cli_vmstat(self, lock_server: ServerThread, lock_name: str):
        completed_process = self._run(lock_name, lock_server, '--', 'vmstat', '1', '1')
        stdout = completed_process.stdout.decode().splitlines()

        # procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
        #  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
        #  1  0      0 484936 1067164 3394552    0    0    54    57  214  537  6  2 92  0  0

        assert completed_process.returncode == 0
        assert len(stdout) == 3
        assert stdout[0].strip().startswith('procs ')
        assert stdout[1].strip().startswith('r ')
        assert re.match(r'^[ 0-9]+$', stdout[2])

    def test_cli_vmstat_with_shell(self, lock_server: ServerThread, lock_name: str):
        completed_process = self._run(lock_name, lock_server, '--shell', '--', 'vmstat 1 1')
        stdout = completed_process.stdout.decode().splitlines()

        # procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
        #  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
        #  1  0      0 484936 1067164 3394552    0    0    54    57  214  537  6  2 92  0  0

        assert completed_process.returncode == 0
        assert len(stdout) == 3
        assert stdout[0].strip().startswith('procs ')
        assert stdout[1].strip().startswith('r ')
        assert re.match(r'^[ 0-9]+$', stdout[2])

    def test_cli_vmstat_with_shell_and_pipe(self, lock_server: ServerThread, lock_name: str):
        completed_process = self._run(lock_name, lock_server, '--shell', '--', 'vmstat 1 1 | grep -v procs')
        #  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
        #  1  0      0 484936 1067164 3394552    0    0    54    57  214  537  6  2 92  0  0
        stdout = completed_process.stdout.decode().splitlines()

        assert completed_process.returncode == 0
        assert len(stdout) == 2
        assert stdout[0].strip().startswith('r ')
        assert re.match(r'^[ 0-9]+$', stdout[1])

    def test_cli_fails_lock_not_granted(self, lock_server: ServerThread, lock_name: str):
        lock_client = lock_server.get_client()
        lock_client.connect()
        assert lock_client.lock(lock_name)

        completed_process = self._run(lock_name, lock_server, '--', 'vmstat', '1', '1')
        assert completed_process.returncode == tnl_do.ERR_LOCK_NOT_GRANTED

    def test_cli_fails_file_not_found(self, lock_server: ServerThread, lock_name: str):
        completed_process = self._run(lock_name, lock_server, '--', '/non/existing/binary', '1', '1')
        assert completed_process.returncode == tnl_do.ERR_FILE_NOT_FOUND

    def test_cli_fails_with_invalid_options(self, lock_server: ServerThread, lock_name: str):
        completed_process = self._run(lock_name, lock_server, '--shell', '--', 'vmstat', 'other-arg')
        assert completed_process.returncode == tnl_do.ERR_INVALID_OPTIONS

    def test_cli_fails_with_connection_refused(self, lock_server: ServerThread, lock_name: str):
        lock_client = LockClient("localhost", port=lock_server.port + 1)  # assume this is free
        with pytest.raises(ConnectionRefusedError):
            lock_client.connect()
        completed_process = self._run(
            lock_name, lock_server,
            '--port={port}'.format(port=lock_server.port + 1),
            '--', 'vmstat', '1', '1')
        assert completed_process.returncode == tnl_do.ERR_CONNECTION_REFUSED

    def test_cli_fails_with_exit_status_of_command(self, lock_server: ServerThread, lock_name: str):
        completed_process = self._run(lock_name + '1', lock_server, '--shell', 'exit 5')
        assert completed_process.returncode == 5

        completed_process = self._run(lock_name + '2', lock_server, '--shell', 'exit 8')
        assert completed_process.returncode == 8

    def test_cli_uses_environment_variable(self, free_tcp_port):
        args = [
            'timeout', '1s',
            'env', 'TCPNETLOCK_PORT={port}'.format(port=free_tcp_port),
            'python', '-m', 'tcpnetlock.cli.tnl_do',
            '--',
            'vmstat', '1',
        ]
        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert completed_process.returncode == tnl_do.ERR_CONNECTION_REFUSED
