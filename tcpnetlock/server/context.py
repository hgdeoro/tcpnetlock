import collections
import threading
import typing

from tcpnetlock.common import Counter
from tcpnetlock.server.lock import Lock


class Context:

    def __init__(self):
        self._global_lock = threading.Lock()
        """Global lock to serialize modification of LOCKS"""

        self._locks = collections.defaultdict(Lock)
        """This dict contains the Lock instances"""

        self._requests_count = Counter()
        """How many requests were accepted"""

        self._lock_acquired_count = Counter()
        """How many times a lock was acquired"""

        self._lock_not_acquired_count = Counter()
        """How many times a lock was NOT acquired"""

    @property
    def global_lock(self) -> threading.Lock:
        return self._global_lock

    @property
    def locks(self) -> typing.Dict[str, Lock]:
        return self._locks

    @property
    def requests_count(self) -> Counter:
        return self._requests_count

    @property
    def lock_acquired_count(self) -> Counter:
        return self._lock_acquired_count

    @property
    def lock_not_acquired_count(self) -> Counter:
        return self._lock_not_acquired_count

    def counters(self):
        return {
            'requests_count': self._requests_count.count,
            'lock_acquired_count': self._lock_acquired_count.count,
            'lock_not_acquired_count': self._lock_not_acquired_count.count,
        }
