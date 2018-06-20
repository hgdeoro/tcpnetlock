import logging
import queue
import subprocess
import sys
import threading

import tcpnetlock.constants
from tcpnetlock.client import client
from tcpnetlock.server import server
from tcpnetlock.cli import common

logger = logging.getLogger(__name__)


class Main(common.BaseMain):

    ERR_INVALID_OPTIONS = 2  # like unix commands
    ERR_LOG_NOT_GRANTED = 123
    ERR_EXECUTING_COMMAND = 124
    ERR_CONNECTION_REFUSED = 125
    ERR_FILE_NOT_FOUND = 127  # like bash

    def add_app_arguments(self):
        parser = self.parser
        parser.add_argument("--lock-name",
                            help="Name of the lock to acquire")

        parser.add_argument("--host",
                            default='localhost')

        parser.add_argument("--port",
                            default=server.TCPServer.DEFAULT_PORT,
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

        parser.add_argument("--shell",
                            default=False,
                            action='store_true',
                            help="Invoke the command with a shell (useful if you're using piping or redirecting)")

        parser.add_argument("command",
                            nargs='+',
                            help="Command to execute (if lock is granted)")

    def validate_and_fix_parameters(self):
        assert self.args

        # --- Get 'command' to use (depending on value of '--shell')
        if self.args.shell:
            if len(self.args.command) != 1:
                self.parser.error("When invoking with --shell, you should provide a SINGLE command. "
                                  "If you're having problems to achieve that, try wrapping it with quotes.")
                sys.exit(self.ERR_INVALID_OPTIONS)

        # --- Get 'lock name' to use (provided by user, or generated from command)
        if not self.args.lock_name:
            temporary = ' '.join(self.args.command)
            temporary = temporary.replace(' ', '_')
            temporary = temporary.replace('.', '_')
            temporary = temporary.replace('/', '_')
            temporary = temporary.strip('_')
            matches = tcpnetlock.constants.VALID_CHARS_IN_LOCK_NAME_RE.findall(temporary)
            self.args.lock_name = ''.join(matches)

            logger.info("Generated lock name '%s' (from provided command '%s')", self.args.lock_name, self.args.command)

            if not self.args.lock_name:
                self.parser.error("Couldn't create a lock name from the command. "
                                  "You must specify the lock name with --lock-name")
                sys.exit(self.ERR_INVALID_OPTIONS)

    def start_keepalive_thread(self, lock_client: client.LockClient):
        keepalive_queue = queue.Queue()

        def loop_keepalives():
            while True:
                logger.debug("Sleeping for %s before sending keep-alive", self.args.keep_alive_secs)
                for _ in range(self.args.keep_alive_secs):
                    try:
                        msg = keepalive_queue.get(block=True, timeout=1)
                        if msg is None:
                            logger.info("Shutting down keepalive thread...")
                            return
                        else:
                            logger.warning("Invalid message '%s' received from Queue. This is rare.", msg)
                    except queue.Empty:
                        pass
                logger.info("Sending keepalive")
                lock_client.keepalive()

        keepalive_thread = threading.Thread(target=loop_keepalives, daemon=True)
        keepalive_thread.start()

        return keepalive_thread, keepalive_queue

    def stop_keepalive_thread(self, keepalive_thread, keepalive_queue):
        if keepalive_thread is None or keepalive_queue is None:
            return
        try:
            keepalive_queue.put(None)
            keepalive_thread.join(2)
            if keepalive_thread.is_alive():
                logger.warning("keepalive_thread still alive: %s", keepalive_thread)
        except:  # noqa: E722 we need to ignore any error
            logger.warning("Error occurred while stopping background thread")

    def main(self):
        self.validate_and_fix_parameters()

        # --- Try to get lock
        lock_client = client.LockClient(self.args.host, self.args.port, client_id=self.args.client_id)
        try:
            lock_client.connect()
        except ConnectionRefusedError:
            logger.error("Connection refused. Server: '%s:%s'", self.args.host, self.args.port)
            sys.exit(self.ERR_CONNECTION_REFUSED)

        granted = lock_client.lock(self.args.lock_name)
        if not granted:
            logger.info("Lock '%s' not granted. Exiting...", self.args.lock_name)
            sys.exit(self.ERR_LOG_NOT_GRANTED)

        # --- Send keepalive from thread
        if self.args.keep_alive:
            keepalive_thread, keepalive_queue = self.start_keepalive_thread(lock_client)
        else:
            keepalive_thread = keepalive_queue = None

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
            sys.exit(self.ERR_FILE_NOT_FOUND)
        except KeyboardInterrupt:
            pass

        # --- Cleanup
        self.stop_keepalive_thread(keepalive_thread, keepalive_queue)

        # Release AFTER keepalive thread is stopped.
        # Otherwise, the 2 threads could be concurrently reading/writing to the socket
        lock_client.release()

        # --- Exit with same 'exit status' of the process we have just ran
        if completed_process:
            sys.exit(completed_process.returncode)
        else:
            sys.exit(self.ERR_EXECUTING_COMMAND)  # something happened (including KeyboardInterrupt)


def main():
    Main().run(args=sys.argv[1:])


if __name__ == '__main__':
    main()
