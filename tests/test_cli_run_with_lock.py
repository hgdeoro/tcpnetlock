"""
Tests for `tcpnetlock.client` and `tcpnetlock.server` packages.
"""

import subprocess

from .test_utils import lock_server
from .test_utils import ServerThread

assert lock_server


def test_cli(lock_server: ServerThread):
    args = ('python', '-m', 'tcpnetlock.cli.run_with_lock',
            '--host=localhost',
            '--port={port}'.format(port=lock_server.port),
            '--lock-name=vmstat',
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

