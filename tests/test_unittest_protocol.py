"""
Unittests for `tcpnetlock.protocol` package.
"""

import socket
from unittest import mock

import pytest

from tcpnetlock.common import ClientDisconnected
from tcpnetlock.protocol import Protocol


class TestProtocol:

    def test_non_blocking_protocol(self):
        mock_socket = mock.Mock()
        mock_socket.recv = mock.MagicMock(side_effect=[socket.timeout()])
        protocol = Protocol(mock_socket)
        line = protocol.readline(0.1)
        assert line is None

    def test_reading_full_line_non_blocking(self):
        mock_socket = mock.Mock()
        mock_socket.recv = mock.MagicMock(side_effect=["full-line\n".encode()])
        protocol = Protocol(mock_socket)
        line = protocol.readline(0.1)
        assert line == 'full-line'

    def test_reading_full_line_blocking(self):
        mock_socket = mock.Mock()
        mock_socket.recv = mock.MagicMock(side_effect=["full-line\n".encode()])
        protocol = Protocol(mock_socket)
        line = protocol.readline()
        assert line == 'full-line'

    def test_reading_partial_line_blocking(self):
        mock_socket = mock.Mock()
        mock_socket.recv = mock.MagicMock(side_effect=["partial-".encode(),
                                                       "line\n".encode()])
        protocol = Protocol(mock_socket)
        line = protocol.readline()
        assert line == 'partial-line'

    def test_reading_partial_line_non_blocking(self):
        mock_socket = mock.Mock()
        mock_socket.recv = mock.MagicMock(side_effect=["partial-".encode(),
                                                       "line\n".encode()])
        protocol = Protocol(mock_socket)
        line = protocol.readline(0.1)
        assert line == 'partial-line'

    def test_disconnect_is_detected_non_blocking(self):
        mock_socket = mock.Mock()
        mock_socket.recv = mock.MagicMock(side_effect=["partial-".encode(),
                                                       ''.encode()])
        protocol = Protocol(mock_socket)

        with pytest.raises(ClientDisconnected):
            protocol.readline(0.1)

    def test_disconnect_is_detected_blocking(self):
        mock_socket = mock.Mock()
        mock_socket.recv = mock.MagicMock(side_effect=["partial-".encode(),
                                                       ''.encode()])
        protocol = Protocol(mock_socket)

        with pytest.raises(ClientDisconnected):
            protocol.readline()
