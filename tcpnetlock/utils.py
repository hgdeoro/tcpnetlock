import logging
import socket


logger = logging.getLogger(__name__)


def get_line(sock, timeout=30):
    binary_data = bytearray()
    # FIXME: this way of implementing timeout is easy and simple, but not very accurate
    # since_try_get_line() will return earlier than 1 sec.
    for _ in range(timeout):
        line = try_get_line(sock, binary_data, timeout=1)
        if line:
            return line
    return None


def try_get_line(sock: socket.socket, binary_data: bytearray, timeout=None, recv_size=1):
    # We need 'recv_size = 1' because we don't handle (yet) the case were
    # client sends 'lock1\nrelease\n'
    # FIXME: re-implement parser, in way that handles correclty lock1\nrelease\n'
    recv_size = 1
    """
    * timeout=None -> disable timeout and red (will BLOCK until we get data)
    * timeout=x -> set timeout of x and red
    """
    if timeout:
        logger.debug('Setting socket timeout to %s', timeout)
        sock.settimeout(timeout)
    else:
        logger.debug('Disabling socket timeout (will block)')
        sock.settimeout(None)

    logger.debug('Reading data...')
    try:
        rr = sock.recv(recv_size)
    except socket.timeout:
        rr = None

    logger.debug("Data received: %s", rr)
    if rr:
        binary_data.extend(rr)

    logger.debug("binary_data: '%s'", binary_data)
    try:
        # FIXME: assuming decode() on partial data works and is safe on utf-8. IS THIS TRUE? Use ASCII otherwise
        potential_line = binary_data.decode()
    except UnicodeDecodeError:
        logger.debug("decoded failed for binary_data '%s'", binary_data)
        return None

    if potential_line.endswith('\n'):
        assert len(potential_line.splitlines()) == 1
        return potential_line.strip()

    return None
