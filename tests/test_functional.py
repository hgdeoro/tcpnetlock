"""
Tests for `tcpnetlock.client` and `tcpnetlock.server` packages.
"""
import uuid

import pytest

from tcpnetlock import common
from tcpnetlock import constants
from tcpnetlock.client.client import LockClient
from .test_utils import BaseTest
from .test_utils import ServerThread
from .test_utils import lock_server

assert lock_server


class TestLock(BaseTest):

    def test_server_is_alive(self, lock_server: ServerThread):
        """Test the test server is actually running"""
        assert lock_server.is_alive()
        client = lock_server.get_client()
        client.connect()
        client.ping()

    def test_connect_and_get_lock_works(self, lock_server):
        """Test that a lock can be acquired"""
        client = lock_server.get_client()
        client.connect()
        acquired = client.lock(uuid.uuid4().hex)
        assert acquired
        assert client.acquired
        client.close()

    def test_connect_and_get_lock_with_client_id_works(self, lock_server):
        """Test that a lock can be acquired"""
        name = uuid.uuid4().hex
        client_id = uuid.uuid4().hex

        client = lock_server.get_client(client_id=client_id)
        client.connect()
        acquired = client.lock(name)
        assert acquired
        client.close()

    def test_get_two_different_lock(self, lock_server):
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

    def test_lock_twice_fails(self, lock_server):
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
        assert not client_2.acquired

        client_1.close()
        client_2.close()

    def test_release_lock_and_re_acquire(self, lock_server):
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

        lucky_client = self.get_client_with_lock_acquired(lock_server, name)
        assert lucky_client  # We got a client that re-acquired the lock

    def test_lock_is_released_when_client_closes_connection(self, lock_server):
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
        lucky_client = self.get_client_with_lock_acquired(lock_server, name)
        assert lucky_client

    def test_server_rejects_invalid_lock_name(self, lock_server, monkeypatch):
        """Test that server do not accept invalid lock name"""
        invalid_names = (
            '.starts-with-space',
            'contains space',
            'contains%invalid%chars',
        )

        for invalid in invalid_names:
            client = lock_server.get_client()
            client.connect()

            with monkeypatch.context() as mp:
                mp.setattr(common.Utils, 'valid_lock_name', lambda x: True)
                acquired = client.lock(invalid)

            assert not acquired, "Lock granted for invalid lock name: '{invalid}'".format(invalid=invalid)
            client.close()

    def test_server_accept_valid_lock_name(self, lock_server, monkeypatch):
        """Test that server DO accept valid lock name"""
        valid_names = (
            'valid1--name',
            'valid2-name-8',
            'valid3_name',
            ' space4_is_ignored',
            'space5_is_ignored ',
            ' space6_is_ignored ',
        )

        for valid in valid_names:
            client = lock_server.get_client()
            client.connect()

            with monkeypatch.context() as mp:
                mp.setattr(common.Utils, 'valid_lock_name', lambda x: True)
                acquired = client.lock(valid)

            assert acquired, "Lock NOT granted for valid lock name: '{valid}'".format(valid=valid)
            client.close()

    def test_client_fails_with_invalid_lock_name(self, lock_server):
        """Test that client fails with invalid lock name"""
        invalid_names = (
            '.starts-with-space',
            'contains space',
            'contains%invalid%chars',
        )

        client = lock_server.get_client()
        client.connect()
        for invalid in invalid_names:
            with pytest.raises(common.InvalidLockNameError):
                client.lock(invalid)
        client.close()

    def test_client_fails_with_invalid_client_id(self):
        """Test that client fails with invalid client id"""
        invalid_client_ids = (
            'contains.point',
            'contains space',
            'contains%invalid%chars',
        )

        for invalid in invalid_client_ids:
            with pytest.raises(common.InvalidClientIdError):
                LockClient(client_id=invalid)


class TestWithLockGranted(BaseTest):

    def test_server_accept_keepalives(self, lock_server):
        """Test that server accept keepalives"""
        client = lock_server.get_client()
        client.connect()
        acquired = client.lock(uuid.uuid4().hex)
        assert acquired
        for _ in range(2):
            client.keepalive()
        client.close()

    def test_server_reports_invalid_action(self, lock_server):
        """Test that server reports an invalid action was sent while holding the lock"""
        client = lock_server.get_client()
        client.connect()
        acquired = client.lock(uuid.uuid4().hex)
        assert acquired
        client._protocol.send('invalid:action')
        line = client._protocol.readline(0.5)
        assert line == constants.RESPONSE_INVALID_ACTION

        # even after en invalid action, keep alive should continue working
        client.keepalive()
        client.close()


class TestAction(BaseTest):

    def test_server_rejects_invalid_action(self, lock_server):
        """Test that server report invalid action"""
        client = lock_server.get_client()
        client.connect()
        client._protocol.send('invalid:action')
        line = client._protocol.readline()
        assert line == constants.RESPONSE_INVALID_ACTION

    def test_server_rejects_invalid_request(self, lock_server):
        """Test that server report invalid request"""
        client = lock_server.get_client()
        client.connect()
        client._protocol.send(',param:value')
        line = client._protocol.readline()
        assert line == "bad-request"
