import logging

from tcpnetlock import constants as const
from tcpnetlock.action import Action
from tcpnetlock.protocol import Protocol
from tcpnetlock.utils import ignore_client_disconnected_exception

logger = logging.getLogger(__name__)


__all__ = [
    'ShutdownActionHandler',
    'PingActionHandler',
    'InvalidLockActionHandler',
    'LockNotGrantedActionHandler',
    'LockGrantedActionHandler',
    'InnerReleaseLockActionHandler',
    'InnerKeepAliveActionHandler',
]


class ActionHandler:
    def __init__(self, protocol: Protocol, action: Action):
        self.protocol = protocol
        self.action = action


class ShutdownActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.server = kwargs.pop('server')
        super().__init__(*args, **kwargs)

    def can_proceed(self):
        # FIXME: assert connections came from localhost
        return True

    def handle_action(self):
        if not self.can_proceed():
            pass  # FIXME: do something
        self.protocol.send(const.RESPONSE_SHUTTING_DOWN)
        self.protocol.close()
        self.server.shutdown()


class PingActionHandler(ActionHandler):

    def handle_action(self):
        self.protocol.send(const.RESPONSE_PONG)
        self.protocol.close()


class InvalidLockActionHandler(ActionHandler):

    def handle_action(self):
        logger.warning("Received invalid lock name: '%s'", self.action.action)
        self.protocol.send(const.RESPONSE_ERR + ',invalid lock name')
        self.protocol.close()


class LockNotGrantedActionHandler(ActionHandler):

    def handle_action(self):
        logger.info("Lock NOT granted: %s", self.action.action)
        self.protocol.send(const.RESPONSE_LOCK_NOT_GRANTED)
        self.protocol.close()


class LockGrantedActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        super().__init__(*args, **kwargs)

    @ignore_client_disconnected_exception
    def handle_action(self):
        self.lock.update(self.action.name, self.action.params.get('client-id'))
        self.protocol.send(const.RESPONSE_OK)

        while True:
            line = self.protocol.readline(timeout=1.0)
            if line is None:
                continue

            inner_action = Action.from_line(line)
            logger.debug("Inner action: '%s' for lock %s", inner_action, self.lock)

            if inner_action.name == const.ACTION_RELEASE:
                return InnerReleaseLockActionHandler(self.protocol, inner_action, lock=self.lock).handle_action()
            if inner_action.name == const.ACTION_KEEPALIVE:
                InnerKeepAliveActionHandler(self.protocol, inner_action, lock=self.lock).handle_action()
            else:
                logger.warning("Ignoring unknown action '%s' for lock: %s", inner_action.name, self.lock)


class InnerReleaseLockActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        super().__init__(*args, **kwargs)

    def handle_action(self):
        logger.info("Releasing lock: %s", self.lock)
        self.protocol.send(const.RESPONSE_RELEASED)
        self.protocol.close()


class InnerKeepAliveActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        super().__init__(*args, **kwargs)

    def handle_action(self):
        logger.debug("Received keepalive from client. Lock: %s", self.lock)
        self.protocol.send(const.RESPONSE_STILL_ALIVE)
