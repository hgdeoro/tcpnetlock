import re

RESPONSE_OK = 'ok'
RESPONSE_ERR = 'err'
RESPONSE_INVALID_ACTION = 'bad-action'
RESPONSE_INVALID_REQUEST = 'bad-request'
RESPONSE_LOCK_NOT_GRANTED = 'not-granted'
RESPONSE_RELEASED = 'released'
RESPONSE_SHUTTING_DOWN = 'shutting-down'
RESPONSE_PONG = 'pong'
RESPONSE_STILL_ALIVE = 'alive'

ACTION_LOCK = 'lock'
ACTION_RELEASE = 'release'
ACTION_SERVER_SHUTDOWN = '.server-shutdown'
ACTION_PING = '.ping'
ACTION_KEEPALIVE = '.keepalive'

VALID_LOCK_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')
VALID_CLIENT_ID_RE = re.compile(r'^[a-zA-Z0-9_-]+$')
VALID_CHARS_IN_LOCK_NAME_RE = re.compile(r'[a-zA-Z0-9_-]')

NEW_LINE_BINARY = '\n'.encode()
