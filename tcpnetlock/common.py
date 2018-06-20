import functools

import tcpnetlock.constants


def ignore_client_disconnected_exception(f):
    """Swallows ClientDisconnected. Use this in method that can receive this exception but can safely ignore it"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ClientDisconnected:
            pass
    return wrapper


class TcpNetLockException(Exception):
    """
    Base class for exceptions.
    """


class ClientDisconnected(TcpNetLockException):
    pass


class InvalidClientIdError(TcpNetLockException):
    """
    Raised by the client if the provided client-id is not valid.
    """


class InvalidLockNameError(TcpNetLockException):
    """
    Raised by the client if the provided LOCK name is not valid.
    """


class Utils:

    @staticmethod
    def valid_lock_name(lock_name):
        """Returns True if the provided lock name is valid"""
        return bool(tcpnetlock.constants.VALID_LOCK_NAME_RE.match(lock_name))

    @staticmethod
    def validate_client_id(client_id, accept_none=True):
        """Raises InvalidClientIdError if client-id is invalid. Pass if it's None"""
        if client_id is None:
            if accept_none:
                return
            else:
                raise InvalidClientIdError("You must provide a client-id")

        if not tcpnetlock.constants.VALID_CLIENT_ID_RE.match(client_id):
            raise InvalidClientIdError("The provided client-id is not valid")
