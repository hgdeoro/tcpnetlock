import argparse
import logging
import subprocess
import sys

from tcpnetlock import client
from tcpnetlock import server

logger = logging.getLogger(__name__)


def main():
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

    # parser.add_argument("--keep-alive",
    #                     default=False,
    #                     action='store_true')
    #
    # parser.add_argument("--keep-alive-secs",
    #                     default=15,
    #                     type=int)

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

    args = parser.parse_args()

    # --- Setup logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.info:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # --- Get 'command' to use (depending on value of '--shell')
    if args.shell:
        if len(args.command) != 1:
            parser.error("When invoking with --shell, you should provide a SINGLE command. "
                         "If you're having problems to achieve that, try wrapping it with quotes.")
            sys.exit(1)
        command = args.command[0]
    else:
        command = args.command

    # --- Get 'lock name' to use (provided by user, or generated from command)
    if args.lock_name:
        lock_name = args.lock_name
    else:
        temporary = ' '.join(command)
        temporary = temporary.replace(' ', '_')
        temporary = temporary.replace('.', '_')
        temporary = temporary.replace('/', '_')
        temporary = temporary.strip('_')
        matches = server.VALID_CHARS_IN_LOCK_NAME_RE.findall(temporary)
        lock_name = ''.join(matches)

        logger.info("Generated lock name '%s' (from provided command '%s')", lock_name, command)

        if not lock_name:
            parser.error("Couldn't create a lock name from the command. "
                         "You must specify the lock name with --lock-name")
            sys.exit(1)

    # --- Try to get lock
    lock_client = client.LockClient(args.host, args.port, client_id=args.client_id)
    lock_client.connect()
    granted = lock_client.lock(lock_name)
    if not granted:
        logger.info("Lock '%s' not granted. Exiting...", lock_name)
        sys.exit(9)

    # --- Send keepalive from thread
    # if args.keep_alive:
    #     while True:
    #         logger.debug("Sleeping for %s... (after that, will send a keep-alive)", args.keep_alive_secs)
    #         time.sleep(args.keep_alive_secs)
    #         lock_client.keepalive()
    # else:
    #     while True:
    #         logger.debug("Sleeping for an hour...")
    #         time.sleep(60 * 60)

    # --- Call command
    logger.info("Lock '%s' was granted. Proceeding with command '%s'", lock_name, command)
    completed_process = None
    try:
        completed_process = subprocess.run(command, shell=args.shell, stdout=None, stderr=None, stdin=None, check=False)
    except FileNotFoundError as err:
        sys.stderr.write("ERROR: command not found: '{command}'\n".format(command=err.filename))
        sys.exit(127)
    finally:
        lock_client.release()

    # --- Exit with same 'exit status' of the process we have just ran
    if completed_process:
        sys.exit(completed_process.returncode)
    else:
        sys.exit(125)


if __name__ == '__main__':
    main()
