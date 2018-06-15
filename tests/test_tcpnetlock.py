#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tcpnetlock` package."""
import multiprocessing
import time
import uuid

import pytest
from click.testing import CliRunner

from tcpnetlock import cli
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
        server = LockServer("localhost", 9999)
        server.serve_forever()

    process = multiprocessing.Process(target=start_server)
    process.daemon = True
    process.start()
    _wait_for_server()  # wait until server is ready

    yield process

    client = LockClient()
    client.connect()
    client.server_shutdown()
    client.close()

    process.join(1)
    process.terminate()


def test_server_is_alive(lock_server):
    """Test the test server is actually running"""
    assert lock_server.is_alive()
    client = LockClient()
    client.connect()
    client.ping()


def test_connect_and_get_lock_works(lock_server):
    """Test that a lock can be acquired"""
    client = LockClient()
    client.connect()
    acquired = client.lock(uuid.uuid4().hex)
    assert acquired
    client.close()


def test_get_two_different_lock(lock_server):
    """Test that two different locks can be acquired"""
    client = LockClient()
    client.connect()
    acquired = client.lock(uuid.uuid4().hex)
    assert acquired
    client.close()

    client2 = LockClient()
    client2.connect()
    acquired = client2.lock(uuid.uuid4().hex)
    assert acquired
    client2.close()


def test_lock_twice(lock_server):
    """Test that a locks can NOT be acquired twice"""
    name = uuid.uuid4().hex

    client1 = LockClient()
    client1.connect()
    acquired = client1.lock(name)
    assert acquired

    client2 = LockClient()
    client2.connect()
    acquired = client2.lock(name)
    assert not acquired

    client1.close()
    client2.close()


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'tcpnetlock.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
