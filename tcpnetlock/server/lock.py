import threading
import time


class Lock:

    def __init__(self):
        self._lock = threading.Lock()
        self._name = None
        self._timestamp = 0
        self._client_id = None

    def acquire_non_blocking(self):
        return self._lock.acquire(blocking=False)

    def update(self, lock_name, client_id):
        if self._name is None:
            self._name = lock_name
        else:
            assert self._name == lock_name

        self._timestamp = time.monotonic()
        self._client_id = client_id

    def release(self):
        self._lock.release()

    @property
    def locked(self):
        return self._lock.locked()

    @property
    def age(self):
        return time.monotonic() - self._timestamp

    def __str__(self):
        return "Lock: '{name}', client-id: '{client}', age: {age}".format(
            name=self._name, client=self._client_id or '', age=int(self.age))
