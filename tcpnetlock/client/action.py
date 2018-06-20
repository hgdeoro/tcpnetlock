import logging

from tcpnetlock.protocol import Protocol

logger = logging.getLogger(__name__)


class ClientAction:

    GENERATE_CUSTOM_MESSAGE = False

    def __init__(self, protocol: Protocol, message: str, valid_responses: list):
        self.protocol = protocol
        self.message = message
        self.valid_responses = valid_responses

        assert self.protocol
        assert self.message or self.GENERATE_CUSTOM_MESSAGE
        assert len(self.valid_responses)

    def parse_and_validate_response(self, line: str):
        response_code, *ignored = line.split(",", maxsplit=1)
        assert response_code in self.valid_responses,\
            "Invalid response: '{response_code}'. Valid responses: {valid_response_codes}. Full line: {line}".format(
                response_code=response_code,
                valid_response_codes=self.valid_responses,
                line=line
            )
        return response_code

    def read_valid_response(self):
        line = self.protocol.readline()
        response_code = self.parse_and_validate_response(line)
        return response_code

    def get_message(self, **kwargs):
        return self.message

    def handle(self, **kwargs):
        message = self.get_message(**kwargs)
        logger.debug("Sending message to server: %s", message)
        self.protocol.send(message)
        return self.read_valid_response()


class AcquireLockClientAction(ClientAction):

    GENERATE_CUSTOM_MESSAGE = True

    def get_message(self, lock_name, **kwargs):
        client_id = kwargs.pop('client_id')
        message = "lock,name:{lock_name}".format(lock_name=lock_name)
        if client_id:
            message += ",client-id:{client_id}".format(client_id=client_id)
        return message
