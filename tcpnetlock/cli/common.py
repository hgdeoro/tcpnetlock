import argparse
import logging

logger = logging.getLogger(__name__)


class BaseMain:

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.args = None

    def add_logging_arguments(self):
        self.parser.add_argument(
            "--debug",
            default=False,
            action='store_true')

        self.parser.add_argument(
            "--info",
            default=False,
            action='store_true')

    def add_app_arguments(self):
        raise NotImplementedError()

    def create_parser(self):
        self.add_app_arguments()
        self.add_logging_arguments()

    def create_args(self, args):
        assert self.parser
        self.args = self.parser.parse_args(args)

    def setup_logging(self):
        assert self.args
        if self.args.debug:
            logging.basicConfig(level=logging.DEBUG)
        elif self.args.info:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)

    def run(self, args):
        self.create_parser()
        self.create_args(args)
        self.setup_logging()
        self.main()

    def main(self):
        raise NotImplementedError()


class PositiveInteger:

    def __init__(self, allow_zero=True):
        self.allow_zero = allow_zero

    def __call__(self, value):
        int_value = int(value)
        if self.allow_zero:
            if int_value < 0:
                raise argparse.ArgumentTypeError("{value} is an invalid positive int value".format(value=int_value))
        else:
            if int_value <= 0:
                raise argparse.ArgumentTypeError("{value} is an invalid positive int value".format(value=int_value))

        return int_value


"""
Example:


class Main(utils.BaseMain):

    def add_app_arguments(self):
        parser = self.parser
        parser.add_argument("--host",
                            default='localhost')

        parser.add_argument("--port",
                            default=server.TCPServer.DEFAULT_PORT,
                            type=int)

    def main(self):
        pass

def main():
    Main().run(args=sys.argv[1:])


if __name__ == '__main__':
    main()


"""
