#!/bin/bash

# --------------------------------------------------------------------------------------------------------------
# Documentation
# --------------------------------------------------------------------------------------------------------------
#
# ATTENTION: this script should be SOURCED. Here we define 2 functions to interact to TPPNetLock from shell script
#
# lock_in_bg() : tries to acquire lock. EXITS if lock can't be acquired, return control back if lock was granted.
#                A process is sent to background (to keep the TCP connection to the server, and thus, keep
#                the ownership of the lock).
#                TRAPs are registered to kill the background process and delete temporary files:
#                 - EXIT
#                 - SIGINT
#                 - SIGTERM
#
# release_lock() : releases the lock.
#
# The lock will also be released automatically if the client is killed (because the TCP connection will be closed and
#  then the server will release the lock)
#
# Configuration of the CLIENT is done through environment variables:
#
# - TCPNETLOCK_PORT (defaults to 9999)
# - TCPNETLOCK_HOST (defauls to 'localhost')
# - TCPNETLOCK_CLIENT_ID (default derivated from shell script filename + hostname)
# - TCPNETLOCK_LOCK_NAME (default derivated from shell script filename)
#
# And to modify default behaviour of this script, you can use:
# - TCPNETLOCK_KEEP_LOG : set to '1' to keep the log file where output of client was saved
# - TCPNETLOCK_DUMP_LOG : set to '1' to dump the log of the client
#
#
# --------------------------------------------------------------------------------------------------------------
# TODO
# --------------------------------------------------------------------------------------------------------------
# - BUG: script fails if an invalid lock name is provided
#

EXIT_CONNECTION_ERROR=3
EXIT_CONNECTION_INVALID_VALUE=4
EXIT_LOCK_NOT_GRANTED=7
EXIT_LOCK_INVALID_RESPONSE=6
EXIT_SIGHANDLER=8


function lock_in_bg() {

    this_file_name_safe="$(echo $(basename $0) | tr . - | sed 's/[^0-9a-zA-Z_-]*//g')"
    # configuration variables (can be overidden by user)
	export TCPNETLOCK_PORT=${TCPNETLOCK_PORT:-9999}
	export TCPNETLOCK_HOST=${TCPNETLOCK_HOST:-localhost}
	export TCPNETLOCK_CLIENT_ID=${TCPNETLOCK_CLIENT_ID:-"${this_file_name_safe}-at-$(hostname)"}
	export TCPNETLOCK_LOCK_NAME=${TCPNETLOCK_LOCK_NAME:-${this_file_name_safe}}

	# configuration for this script
	TCPNETLOCK_KEEP_LOG="${TCPNETLOCK_KEEP_LOG:-0}"
	TCPNETLOCK_DUMP_LOG="${TCPNETLOCK_DUMP_LOG:-0}"

	# internal variables
	TCPNETLOCK_TMP_LOG=$(mktemp)
	TCPNETLOCK_TMP_PID='0'

	echo "TNL> Logging to $TCPNETLOCK_TMP_LOG"
	trap '_cleanup' EXIT
	trap '_cleanup ; exit $EXIT_SIGHANDLER' SIGINT SIGTERM

    echo "TNL> Trying to acquire lock '$TCPNETLOCK_LOCK_NAME'"
	python -m tcpnetlock.client --debug --host=$TCPNETLOCK_HOST --port=$TCPNETLOCK_PORT --print-marks \
		--client-id=$TCPNETLOCK_CLIENT_ID --keep-alive $TCPNETLOCK_LOCK_NAME > $TCPNETLOCK_TMP_LOG 2>&1 & TCPNETLOCK_TMP_PID=$!
	echo "TNL> Background PID: $TCPNETLOCK_TMP_PID"

	connection_full_line=''
	while [ -z "$connection_full_line" ] ; do
		sleep 0.2  # an initial wait won't hurt
		connection_full_line="$(egrep -o 'MARK,CONNECTION,.+,END' $TCPNETLOCK_TMP_LOG)"
	done
	connection=$(echo "$connection_full_line" | cut -d , -f 3)
	case "$connection" in
		"OK") ;;
		"REFUSED"|"REFUSED") echo "TNL> ERROR: connection to server failed." ; exit $EXIT_CONNECTION_ERROR ;;
		*) echo "TNL> ERROR: invalid value for CONNECTION: $connection"; exit $EXIT_CONNECTION_INVALID_VALUE ;;
	esac

	acquire_status_full_line=''
	while [ -z "$acquire_status_full_line" ] ; do
		sleep 0.2  # an initial wait won't hurt
		acquire_status_full_line="$(egrep -o 'MARK,LOCK_RESULT,LOCK:.+,ACQUIRED:.+,END' $TCPNETLOCK_TMP_LOG)"
	done
	acquired=$(echo "$acquire_status_full_line" | cut -d , -f 4 | cut -d : -f 2)
	case "$acquired" in
		"True") return 0 ;;
		"False") echo "TNL> ERROR: lock not granted. Exiting." ; exit $EXIT_LOCK_NOT_GRANTED ;;
		*) echo "TNL> ERROR: invalid value for acquired: $acquired"; exit $EXIT_LOCK_INVALID_RESPONSE ;;
	esac

}

function release_lock() {
    _cleanup
	trap '' EXIT
	trap '' SIGINT SIGTERM
}

function _cleanup() {
    echo "TNL> Cleanup pids $TCPNETLOCK_TMP_PID and $TCPNETLOCK_TMP_LOG"
    ps --no-headers -q $TCPNETLOCK_TMP_PID | grep -q $TCPNETLOCK_TMP_PID && {
        kill $TCPNETLOCK_TMP_PID  # lock is released here
    }
    test "$TCPNETLOCK_DUMP_LOG" = '0' || {
        _print_logs
    }
    test -e $TCPNETLOCK_TMP_LOG && test $TCPNETLOCK_KEEP_LOG = '0' && /bin/rm -f $TCPNETLOCK_TMP_LOG
}

function _print_logs() {
    test -e $TCPNETLOCK_TMP_LOG || return
    echo "TNL> ---------- Marks found in log file ----------"
    egrep -o 'MARK,LOCK_RESULT,LOCK:.+,ACQUIRED:.+,END' $TCPNETLOCK_TMP_LOG
    echo "TNL> ---------- Full contents of log file ----------"
    cat $TCPNETLOCK_TMP_LOG
    echo "TNL> ------------------------------"
}
