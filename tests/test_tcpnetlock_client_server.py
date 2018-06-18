"""
Tests for `tcpnetlock.client` and `tcpnetlock.server` packages.
"""

import time
import uuid
from unittest import mock

from .test_utils import lock_server
from .test_utils import ServerThread

assert lock_server


def test_server_is_alive(lock_server: ServerThread):
    """Test the test server is actually running"""
    assert lock_server.is_alive()
    client = lock_server.get_client()
    client.connect()
    client.ping()


def test_connect_and_get_lock_works(lock_server):
    """Test that a lock can be acquired"""
    client = lock_server.get_client()
    client.connect()
    acquired = client.lock(uuid.uuid4().hex)
    assert acquired
    client.close()


def test_connect_and_get_lock_with_client_id_works(lock_server):
    """Test that a lock can be acquired"""
    name = uuid.uuid4().hex
    client_id = uuid.uuid4().hex

    client = lock_server.get_client(client_id=client_id)
    client.connect()
    acquired = client.lock(name)
    assert acquired
    client.close()


def test_server_accept_keepalives(lock_server):
    """Test that server accept keepalives"""
    client = lock_server.get_client()
    client.connect()
    acquired = client.lock(uuid.uuid4().hex)
    for _ in range(2):
        client.keepalive()
        time.sleep(0.2)
    client.close()


def test_get_two_different_lock(lock_server):
    """Test that two different locks can be acquired"""
    client_1 = lock_server.get_client()
    client_1.connect()
    acquired = client_1.lock(uuid.uuid4().hex)
    assert acquired
    client_1.close()

    client_2 = lock_server.get_client()
    client_2.connect()
    acquired = client_2.lock(uuid.uuid4().hex)
    assert acquired
    client_2.close()


def test_lock_twice_fails(lock_server):
    """Test that a locks can NOT be acquired twice"""
    name = uuid.uuid4().hex

    client_1 = lock_server.get_client()
    client_1.connect()
    acquired = client_1.lock(name)
    assert acquired

    client_2 = lock_server.get_client()
    client_2.connect()
    acquired = client_2.lock(name)
    assert not acquired

    client_1.close()
    client_2.close()


def test_release_lock_and_re_acquire(lock_server):
    """Test that a locks can be acquired again after it's released"""
    name = uuid.uuid4().hex

    # acquire lock
    client_1 = lock_server.get_client()
    client_1.connect()
    acquired = client_1.lock(name)
    assert acquired
    # release lock
    client_1.release()
    client_1.close()

    # re-acquire same lock
    client_2 = lock_server.get_client()
    client_2.connect()
    acquired = client_2.lock(name)
    assert acquired
    client_2.close()


def test_lock_is_released_when_client_closes_connection(lock_server):
    """Test that the server releases the lock if the socket connection is suddenly closed"""
    name = uuid.uuid4().hex

    # acquire lock
    client_1 = lock_server.get_client()
    client_1.connect()
    acquired = client_1.lock(name)
    assert acquired
    # don't release socket, just close the connection
    client_1.close()

    # re-acquire same lock
    acquired = False
    for _ in range(20):
        client_2 = lock_server.get_client()
        client_2.connect()
        acquired = client_2.lock(name)
        if not acquired:
            time.sleep(0.1)
    assert acquired


def test_server_rejects_invalid_lock_name(lock_server):
    """Test that server do not accept invalid lock name"""
    invalid_names = (
        '.starts-with-space',
        'contains space',
        'contains%invalid%chars',
    )

    for invalid in invalid_names:
        client = lock_server.get_client()
        client.valid_lock_name = mock.MagicMock(return_value=True)
        client.connect()
        acquired = client.lock(invalid)
        assert not acquired, "Lock granted for invalid lock name: '{invalid}'".format(invalid=invalid)
        client.close()


def test_server_accept_valid_lock_name(lock_server):
    """Test that server DO accept valid lock name"""
    valid_names = (
        'valid-name',
        'valid-name-8',
        'valid_name',
        ' space_is_ignored',
        'space_is_ignored ',
        ' space_is_ignored ',
    )

    for valid in valid_names:
        client = lock_server.get_client()
        client.valid_lock_name = mock.MagicMock(return_value=True)
        client.connect()
        acquired = client.lock(valid)
        assert acquired, "Lock NOT granted for valid lock name: '{valid}'".format(valid=valid)
        client.close()
