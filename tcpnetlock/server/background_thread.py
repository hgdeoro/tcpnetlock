import logging
import threading
import time

from tcpnetlock.server.context import Context

logger = logging.getLogger(__name__)


class BackgroundThread(threading.Thread):

    daemon = True
    iteration_wait = 5
    min_age = 5

    def __init__(self, context: Context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context = context

    def run(self):
        while True:
            self.cleanup_old_locks()

    def cleanup_old_locks(self):
        logger.info("Cleaning up old locks...")
        for key in self._get_keys():
            try:
                self._check_key(key)
            except:  # noqa: E722 we need to ignore any error
                logger.exception("Exception detected in BackgroundThread while checking key '%s'", key)
        logger.info("Cleaning finished")
        self._wait()

    def _wait(self):
        time.sleep(self.iteration_wait)

    def _get_keys(self):
        # try:
        #     return list(Context.LOCKS.keys())
        # except RuntimeError:
        #     logger.info("RuntimeError detected when trying to get list of keys. "
        #                      "Will retry holding GLOBAL_LOCK", exc_info=True)
        #     with Context.GLOBAL_LOCK:
        #         return list(Context.LOCKS.keys())

        # Always get the GLOBAL_LOCK. It would be ok if we get an exception here, but before using the code above,
        # we must be sure that the iteration done in the code do not prevents the main server modify LOCKS,
        # and that there is NO way that our iteration could generate any inconvenience there.

        with self._context.global_lock:
            return list(self._context.locks.keys())

    def _check_key(self, key):
        lock = self._context.locks[key]
        if lock.locked:
            return
        if lock.age < self.min_age:
            # Here we're evaluating the lock grant age, so, not sure if this makes sense
            return

        ackquired = False
        try:
            ackquired = lock.acquire_non_blocking()
            if not ackquired:
                logger.info("Weird... couldn't get the lock to delete '%s'", key)
                return

            logger.info("Cleaning up key '%s'", key)
            del self._context.locks[key]

        finally:
            if ackquired:
                lock.release()
