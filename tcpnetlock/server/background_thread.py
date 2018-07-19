import logging
import threading
import time

from tcpnetlock.server.context import Context


# logger = logging.getLogger(__name__)


class BackgrounThread(threading.Thread):
    daemon = True
    iteration_wait = 5
    min_age = 5
    logger = logging.getLogger("{}.BackgrounThread".format(__name__))

    def run(self):
        while True:
            self.logger.info("Running cleanup")
            for key in self._get_keys():
                try:
                    self._check_key(key)
                except:  # noqa: E722 we need to ignore any error
                    self.logger.exception("Exception detected in BackgrounThread while checking key '%s'", key)
            time.sleep(self.iteration_wait)

    def _get_keys(self):
        try:
            # May raise 'RuntimeError: dictionary changed size during iteration'
            return list(Context.LOCKS.keys())
        except RuntimeError:
            self.logger.info("RuntimeError detected when trying to get list of keys. "
                             "Will retry holding GLOBAL_LOCK", exc_info=True)
            with Context.GLOBAL_LOCK:
                return list(Context.LOCKS.keys())

    def _check_key(self, key):
        lock = Context.LOCKS[key]
        if lock.locked:
            return
        if lock.age < self.min_age:
            return

        ackquired = False
        try:
            ackquired = lock.acquire_non_blocking()
            if not ackquired:
                self.logger.info("Weird... couldn't get the lock to delete '%s'", key)
                return

            # We got the lock, we can remove it from the dict
            self.logger.info("Cleaning key '%s'", key)
            del Context.LOCKS[key]

        finally:
            if ackquired:
                lock.release()
