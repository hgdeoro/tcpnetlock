#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tcpnetlock` package."""
import threading
import time
import uuid
from unittest import mock

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
    assert not server_thread.is_alive(), "TEST Server didn't shut down cleanly"


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


def test_connect_and_get_lock_with_client_id_works(lock_server):
    """Test that a lock can be acquired"""
    name = uuid.uuid4().hex
    client_id = uuid.uuid4().hex

    client = LockClient(client_id=client_id)
    client.connect()
    acquired = client.lock(name)
    assert acquired
    client.close()


def test_connect_and_get_lock_works(lock_server):
    """Test that a lock can be acquired"""
    client = LockClient()
    client.connect()
    acquired = client.lock(uuid.uuid4().hex)
    for _ in range(5):
        client.keepalive()
        time.sleep(0.5)
    client.close()


def test_get_two_different_lock(lock_server):
    """Test that two different locks can be acquired"""
    client_1 = LockClient()
    client_1.connect()
    acquired = client_1.lock(uuid.uuid4().hex)
    assert acquired
    client_1.close()

    client_2 = LockClient()
    client_2.connect()
    acquired = client_2.lock(uuid.uuid4().hex)
    assert acquired
    client_2.close()


def test_lock_twice_fails(lock_server):
    """Test that a locks can NOT be acquired twice"""
    name = uuid.uuid4().hex

    client_1 = LockClient()
    client_1.connect()
    acquired = client_1.lock(name)
    assert acquired

    client_2 = LockClient()
    client_2.connect()
    acquired = client_2.lock(name)
    assert not acquired

    client_1.close()
    client_2.close()


def test_released_lock_and_be_re_acquired(lock_server):
    """Test that a locks can be acquired again after it's released"""
    name = uuid.uuid4().hex

    # acquire lock
    client_1 = LockClient()
    client_1.connect()
    acquired = client_1.lock(name)
    assert acquired
    # release lock
    client_1.release()
    client_1.close()

    # re-acquire same lock
    client_2 = LockClient()
    client_2.connect()
    acquired = client_2.lock(name)
    assert acquired
    client_2.close()


def test_lock_released_when_client_closes_connection(lock_server):
    """Test that a locks can be acquired again after it's released"""
    name = uuid.uuid4().hex

    # acquire lock
    client_1 = LockClient()
    client_1.connect()
    acquired = client_1.lock(name)
    assert acquired
    # don't release socket, just close the connection
    client_1.close()

    # re-acquire same lock
    acquired = False
    for _ in range(20):
        client_2 = LockClient()
        client_2.connect()
        acquired = client_2.lock(name)
        if not acquired:
            time.sleep(0.1)
    assert acquired


def test_server_rejects_invalid_lock_name(lock_server):
    """Test that a locks can be acquired again after it's released"""
    invalid_names = (
        '.starts-with-space',
        'contains space',
        'contains%invalid%chars',
    )

    for invalid in invalid_names:
        client = LockClient()
        client.valid_lock_name = mock.MagicMock(return_value=True)
        client.connect()
        acquired = client.lock(invalid)
        assert not acquired, "Lock granted for invalid lock name: '{invalid}'".format(invalid=invalid)
        client.close()


def test_server_accept_valid_lock_name(lock_server):
    valid_names = (
        'valid-name',
        'valid-name-8',
        'valid_name',
        ' space_is_ignored',
        'space_is_ignored ',
        ' space_is_ignored ',
    )

    for valid in valid_names:
        client = LockClient()
        client.valid_lock_name = mock.MagicMock(return_value=True)
        client.connect()
        acquired = client.lock(valid)
        assert acquired, "Lock NOT granted for valid lock name: '{valid}'".format(valid=valid)
        client.close()
