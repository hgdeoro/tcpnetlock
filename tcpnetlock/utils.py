import functools


def ignore_client_disconnected_exception(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ClientDisconnected:
            pass
    return wrapper


class ClientDisconnected(Exception):
    pass
