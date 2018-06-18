import argparse
import logging

logger = logging.getLogger(__name__)


class BaseMain:

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.args = None

    def add_loggin_arguments(self):
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
        self.add_loggin_arguments()

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
        pass
