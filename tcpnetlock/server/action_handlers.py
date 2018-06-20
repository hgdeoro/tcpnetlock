import logging

from tcpnetlock import constants as const
from tcpnetlock.server.action import Action
from tcpnetlock.protocol import Protocol
from tcpnetlock.common import ignore_client_disconnected_exception

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
        self.server.shutdown()
        self.protocol.close()


class PingActionHandler(ActionHandler):

    def handle_action(self):
        self.protocol.send(const.RESPONSE_PONG)
        self.protocol.close()


class InvalidActionActionHandler(ActionHandler):
    def handle_action(self):
        logger.warning("Received invalid action: '%s'", self.action.name)
        self.protocol.send(const.RESPONSE_INVALID_ACTION)
        self.protocol.close()


class InvalidLockActionHandler(ActionHandler):
    def __init__(self, *args, **kwargs):
        self.lock_name = kwargs.pop('lock_name')
        super().__init__(*args, **kwargs)

    def handle_action(self):
        logger.warning("Received invalid lock name: '%s'", self.lock_name)
        self.protocol.send(const.RESPONSE_ERR + ',invalid lock name')
        self.protocol.close()


class LockNotGrantedActionHandler(ActionHandler):
    def __init__(self, *args, **kwargs):
        self.lock_name = kwargs.pop('lock_name')
        super().__init__(*args, **kwargs)

    def handle_action(self):
        logger.info("Lock NOT granted: %s", self.lock_name)
        self.protocol.send(const.RESPONSE_LOCK_NOT_GRANTED)
        self.protocol.close()


class LockGrantedActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        self.lock_name = kwargs.pop('lock_name')
        super().__init__(*args, **kwargs)
        self.client_id = self.action.params.get('client-id')

    @ignore_client_disconnected_exception
    def handle_action(self):
        self.lock.update(self.lock_name, self.client_id)
        self.protocol.send(const.RESPONSE_OK)

        while True:
            line = self.protocol.readline(timeout=1.0)
            if line is None:
                continue

            inner_action = Action.from_line(line)
            logger.debug("Inner action: '%s' for lock %s", inner_action, self.lock)

            # FIXME: handle 'invalid requests' here too

            if inner_action.name == const.ACTION_RELEASE:
                return InnerReleaseLockActionHandler(self.protocol, inner_action, lock=self.lock).handle_action()
            if inner_action.name == const.ACTION_KEEPALIVE:
                InnerKeepAliveActionHandler(self.protocol, inner_action, lock=self.lock).handle_action()
            else:
                InnerInvalidActionActionHandler(self.protocol, inner_action, lock=self.lock).handle_action()


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


class InnerInvalidActionActionHandler(ActionHandler):

    def __init__(self, *args, **kwargs):
        self.lock = kwargs.pop('lock')
        super().__init__(*args, **kwargs)

    def handle_action(self):
        logger.debug("Received invalid action from client. Lock: %s", self.lock)
        self.protocol.send(const.RESPONSE_INVALID_ACTION)
