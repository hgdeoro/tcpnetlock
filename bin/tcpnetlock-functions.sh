#!/bin/bash

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
# Configuration is done thruogh environment variables:
#
# - CLOUDLAB_PORT (defaults to 9999)
# - CLOUDLAB_HOST (defauls to 'localhost')
# - CLOUDLAB_CLIENT_ID (default derivated from shell script filename + hostname)
# - CLOUDLAB_LOCK_NAME (default derivated from shell script filename)
#

EXIT_CONNECTION_ERROR=3
EXIT_CONNECTION_INVALID_VALUE=4
EXIT_LOCK_NOT_GRANTED=7
EXIT_LOCK_INVALID_RESPONSE=6
EXIT_SIGHANDLER=8


function lock_in_bg() {

    this_file_name_safe="$(echo $(basename $0) | tr . - | sed 's/[^0-9a-zA-Z_-]*//g')"
	export CLOUDLAB_PORT=${CLOUDLAB_PORT:-9999}
	export CLOUDLAB_HOST=${CLOUDLAB_HOST:-localhost}
	export CLOUDLAB_CLIENT_ID=${CLOUDLAB_CLIENT_ID:-"${this_file_name_safe}-at-$(hostname)"}
	export CLOUDLAB_LOCK_NAME=${CLOUDLAB_LOCK_NAME:-${this_file_name_safe}}
	CLOUDLAB_TMP_LOG=$(mktemp)
	CLOUDLAB_TMP_PID='0'

	echo "TNL> Logging to $CLOUDLAB_TMP_LOG"
	trap '\
		echo "Cleanup pids $CLOUDLAB_TMP_PID and $CLOUDLAB_TMP_LOG" ; \
		ps --no-headers -q $CLOUDLAB_TMP_PID | grep -q $CLOUDLAB_TMP_PID && kill $CLOUDLAB_TMP_PID ; \
		test -e $CLOUDLAB_TMP_LOG && /bin/rm -f $CLOUDLAB_TMP_LOG \
		' EXIT
	trap '\
		echo "Cleanup pids $CLOUDLAB_TMP_PID and $CLOUDLAB_TMP_LOG" ; \
		ps --no-headers -q $CLOUDLAB_TMP_PID | grep -q $CLOUDLAB_TMP_PID && kill $CLOUDLAB_TMP_PID ; \
		test -e $CLOUDLAB_TMP_LOG && /bin/rm -f $CLOUDLAB_TMP_LOG ; \
		exit $EXIT_SIGHANDLER' SIGINT SIGTERM

    echo "TNL> Trying to acquire lock '$CLOUDLAB_LOCK_NAME'"
	python -m tcpnetlock.client --debug --host=$CLOUDLAB_HOST --port=$CLOUDLAB_PORT --print-marks \
		--client-id=$CLOUDLAB_CLIENT_ID --keep-alive $CLOUDLAB_LOCK_NAME > $CLOUDLAB_TMP_LOG 2>&1 & CLOUDLAB_TMP_PID=$!
	echo "TNL> Background PID: $CLOUDLAB_TMP_PID"

	connection_full_line=''
	while [ -z "$connection_full_line" ] ; do
		sleep 0.2  # an initial wait won't hurt
		connection_full_line="$(egrep -o 'MARK,CONNECTION,.+,END' $CLOUDLAB_TMP_LOG)"
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
		acquire_status_full_line="$(egrep -o 'MARK,LOCK_RESULT,LOCK:.+,ACQUIRED:.+,END' $CLOUDLAB_TMP_LOG)"
	done
	acquired=$(echo "$acquire_status_full_line" | cut -d , -f 4 | cut -d : -f 2)
	case "$acquired" in
		"True") return 0 ;;
		"False") echo "TNL> ERROR: lock not granted. Exiting." ; exit $EXIT_LOCK_NOT_GRANTED ;;
		*) echo "TNL> ERROR: invalid value for acquired: $acquired"; exit $EXIT_LOCK_INVALID_RESPONSE ;;
	esac

}

function release_lock() {
    kill $CLOUDLAB_TMP_PID
    rm $CLOUDLAB_TMP_LOG

	trap '' EXIT
	trap '' SIGINT SIGTERM
}

function _print_logs() {
    test -e $CLOUDLAB_TMP_LOG || return
    echo "TNL> Marks found in log file ----------"
    egrep -o 'MARK,LOCK_RESULT,LOCK:.+,ACQUIRED:.+,END' $CLOUDLAB_TMP_LOG
    echo "TNL> Full contents of log file ----------"
    cat $CLOUDLAB_TMP_LOG
    echo "TNL> ----------"
}
