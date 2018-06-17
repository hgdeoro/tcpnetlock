"""
Tests for `tcpnetlock.client` and `tcpnetlock.server` packages.
"""

import re
import subprocess

from tcpnetlock.cli import run_with_lock

from .test_utils import ServerThread
from .test_utils import lock_server
from .test_utils import lock_name

assert lock_server
assert lock_name


class TestRunWithLock:

    def test_cli_vmstat(self, lock_server: ServerThread, lock_name: str):
        args = ('python', '-m', 'tcpnetlock.cli.run_with_lock',
                '--host=localhost',
                '--port={port}'.format(port=lock_server.port),
                '--lock-name={lock_name}'.format(lock_name=lock_name),
                '--',
                'vmstat', '1', '1')

        # procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
        #  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
        #  1  0      0 484936 1067164 3394552    0    0    54    57  214  537  6  2 92  0  0

        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = completed_process.stdout.decode().splitlines()
        stderr = completed_process.stderr.decode().splitlines()

        assert completed_process.returncode == 0
        assert len(stdout) == 3
        assert stdout[0].strip().startswith('procs ')
        assert stdout[1].strip().startswith('r ')
        assert re.match(r'^[ 0-9]+$', stdout[2])

    def test_cli_vmstat_with_shell(self, lock_server: ServerThread, lock_name: str):
        args = ('python', '-m', 'tcpnetlock.cli.run_with_lock',
                '--host=localhost',
                '--port={port}'.format(port=lock_server.port),
                '--lock-name={lock_name}'.format(lock_name=lock_name),
                '--shell',
                '--',
                'vmstat 1 1')

        # procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
        #  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
        #  1  0      0 484936 1067164 3394552    0    0    54    57  214  537  6  2 92  0  0

        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = completed_process.stdout.decode().splitlines()
        stderr = completed_process.stderr.decode().splitlines()

        assert completed_process.returncode == 0
        assert len(stdout) == 3
        assert stdout[0].strip().startswith('procs ')
        assert stdout[1].strip().startswith('r ')
        assert re.match(r'^[ 0-9]+$', stdout[2])

    def test_cli_vmstat_with_shell_and_pipe(self, lock_server: ServerThread, lock_name: str):
        args = ('python', '-m', 'tcpnetlock.cli.run_with_lock',
                '--host=localhost',
                '--port={port}'.format(port=lock_server.port),
                '--lock-name={lock_name}'.format(lock_name=lock_name),
                '--shell',
                '--',
                'vmstat 1 1 | grep -v procs')

        #  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
        #  1  0      0 484936 1067164 3394552    0    0    54    57  214  537  6  2 92  0  0

        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = completed_process.stdout.decode().splitlines()
        stderr = completed_process.stderr.decode().splitlines()

        assert completed_process.returncode == 0
        assert len(stdout) == 2
        assert stdout[0].strip().startswith('r ')
        assert re.match(r'^[ 0-9]+$', stdout[1])

    def test_cli_fails_log_not_granted(self, lock_server: ServerThread, lock_name: str):
        lock_client = lock_server.get_client()
        lock_client.connect()
        assert lock_client.lock(lock_name)

        args = ('python', '-m', 'tcpnetlock.cli.run_with_lock',
                '--host=localhost',
                '--port={port}'.format(port=lock_server.port),
                '--lock-name={lock_name}'.format(lock_name=lock_name),
                '--shell',
                '--',
                'vmstat 1 1 | grep -v procs')

        #  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
        #  1  0      0 484936 1067164 3394552    0    0    54    57  214  537  6  2 92  0  0

        completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = completed_process.stdout.decode().splitlines()
        stderr = completed_process.stderr.decode().splitlines()

        assert completed_process.returncode == run_with_lock.Main.ERR_LOG_NOT_GRANTED
