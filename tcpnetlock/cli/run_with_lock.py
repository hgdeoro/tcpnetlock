import argparse
import logging
import subprocess
import sys
import threading
import time

from tcpnetlock import client
from tcpnetlock import server

logger = logging.getLogger(__name__)


class Main:

    def __init__(self):
        self.parser = None
        self.args = None

    def create_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--lock-name",
                            help="Name of the lock to acquire")

        parser.add_argument("--host",
                            default='localhost')

        parser.add_argument("--port",
                            default=9999,
                            type=int)

        parser.add_argument("--client-id",
                            default=None,
                            help="Client id to report to the server")

        parser.add_argument("--keep-alive",
                            default=False,
                            action='store_true')

        parser.add_argument("--keep-alive-secs",
                            default=15,
                            type=int)

        parser.add_argument("--debug",
                            default=False,
                            action='store_true')

        parser.add_argument("--info",
                            default=False,
                            action='store_true')

        parser.add_argument("--shell",
                            default=False,
                            action='store_true',
                            help="Invoke the command with a shell (useful if you're using piping or redirecting)")

        parser.add_argument("command",
                            nargs='+',
                            help="Command to execute (if lock is granted)")

        self.parser = parser

    def create_args(self):
        assert self.parser
        self.args = self.parser.parse_args()

    def setup_logging(self):
        assert self.args
        if self.args.debug:
            logging.basicConfig(level=logging.DEBUG)
        elif self.args.info:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)

    def validate_and_fix_parameters(self):
        assert self.args

        # --- Get 'command' to use (depending on value of '--shell')
        if self.args.shell:
            if len(self.args.command) != 1:
                self.parser.error("When invoking with --shell, you should provide a SINGLE command. "
                                  "If you're having problems to achieve that, try wrapping it with quotes.")
                sys.exit(1)

        # --- Get 'lock name' to use (provided by user, or generated from command)
        if not self.args.lock_name:
            temporary = ' '.join(self.args.command)
            temporary = temporary.replace(' ', '_')
            temporary = temporary.replace('.', '_')
            temporary = temporary.replace('/', '_')
            temporary = temporary.strip('_')
            matches = server.VALID_CHARS_IN_LOCK_NAME_RE.findall(temporary)
            self.args.lock_name = ''.join(matches)

            logger.info("Generated lock name '%s' (from provided command '%s')", self.args.lock_name, self.args.command)

            if not self.args.lock_name:
                self.parser.error("Couldn't create a lock name from the command. "
                                  "You must specify the lock name with --lock-name")
                sys.exit(1)

    def run(self):
        self.create_parser()
        self.create_args()
        self.setup_logging()
        self.validate_and_fix_parameters()

        # --- Try to get lock
        lock_client = client.LockClient(self.args.host, self.args.port, client_id=self.args.client_id)
        lock_client.connect()
        granted = lock_client.lock(self.args.lock_name)
        if not granted:
            logger.info("Lock '%s' not granted. Exiting...", self.args.lock_name)
            sys.exit(9)

        # --- Send keepalive from thread
        keepalive_thread = None
        if self.args.keep_alive:
            def loop_keepalives():
                while True:
                    logger.debug("Sleeping for %s before sending keep-alive", self.args.keep_alive_secs)
                    time.sleep(self.args.keep_alive_secs)
                    logger.info("Sending keepalive")
                    lock_client.keepalive()
            keepalive_thread = threading.Thread(target=loop_keepalives, daemon=True)
            keepalive_thread.start()

        # --- Call command
        logger.info("Lock '%s' was granted. Proceeding with command '%s'", self.args.lock_name, self.args.command)
        completed_process = None
        try:
            completed_process = subprocess.run(self.args.command,
                                               shell=self.args.shell,
                                               stdout=None,
                                               stderr=None,
                                               stdin=None,
                                               check=False)
        except FileNotFoundError as err:
            sys.stderr.write("ERROR: command not found: '{command}'\n".format(command=err.filename))
            sys.exit(127)
        except KeyboardInterrupt:
            # FIXME: Handle KeyboardInterrupt !!!
            pass
        finally:
            lock_client.release()

        # --- Finish thread
        if keepalive_thread:
            pass  # FIXME: stop sending keepalives

        # --- Exit with same 'exit status' of the process we have just ran
        if completed_process:
            sys.exit(completed_process.returncode)
        else:
            sys.exit(125)


def main():
    Main().run()


if __name__ == '__main__':
    main()
