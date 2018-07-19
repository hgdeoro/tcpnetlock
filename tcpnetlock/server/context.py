import collections
import threading

from tcpnetlock.common import Counter
from tcpnetlock.server.lock import Lock


# FIXME: we should use a Context INSTANCE, not a class holding global state :/


class Context:

    GLOBAL_LOCK = threading.Lock()
    """Global lock to serialize modification of LOCKS"""

    LOCKS = collections.defaultdict(Lock)
    """This dict contains the Lock instances"""

    REQUESTS_COUNT = Counter()
    """How many requests were accepted"""

    LOCK_ACKQUIRED_COUNT = Counter()
    """How many times a lock was acquired"""

    LOCK_NOT_ACKQUIRED_COUNT = Counter()
    """How many times a lock was NOT acquired"""

    @classmethod
    def counters(cls):
        return {
            'request_count': cls.REQUESTS_COUNT.count,
            'lock_acquired_count': cls.LOCK_ACKQUIRED_COUNT.count,
            'lock_not_acquired_count': cls.LOCK_NOT_ACKQUIRED_COUNT.count,
        }
