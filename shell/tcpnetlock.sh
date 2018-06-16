#!/bin/bash

EXIT_CONNECTION_ERROR=3
EXIT_CONNECTION_INVALID_VALUE=4

function lock_in_bg() {

    # Environment variables user would set:
    # - CLOUDLAB_PORT
    # - CLOUDLAB_HOST
    # - CLOUDLAB_CLIENT_ID
    # - CLOUDLAB_LOCK_NAME

	export CLOUDLAB_PORT=${CLOUDLAB_PORT:-9999}
	export CLOUDLAB_HOST=${CLOUDLAB_HOST:-localhost}
	export CLOUDLAB_CLIENT_ID=${CLOUDLAB_CLIENT_ID:-$(uuidgen)}
	export CLOUDLAB_LOCK_NAME=${CLOUDLAB_LOCK_NAME:-$(echo $(basename $0) | tr . - | sed 's/[^0-9a-zA-Z_-]*//g')}
	export CLOUDLAB_TMP_LOG=$(mktemp)
	export CLOUDLAB_TMP_PID='0'

	echo "Logging to $CLOUDLAB_TMP_LOG"
	trap '\
		echo "Cleanup pids $CLOUDLAB_TMP_PID and $CLOUDLAB_TMP_LOG" ; \
		ps --no-headers -q $CLOUDLAB_TMP_PID | grep -q $CLOUDLAB_TMP_PID && kill $CLOUDLAB_TMP_PID ; \
		test -e $CLOUDLAB_TMP_LOG && /bin/rm -f $CLOUDLAB_TMP_LOG \
		' EXIT
	trap '\
		echo "Cleanup pids $CLOUDLAB_TMP_PID and $CLOUDLAB_TMP_LOG" ; \
		ps --no-headers -q $CLOUDLAB_TMP_PID | grep -q $CLOUDLAB_TMP_PID && kill $CLOUDLAB_TMP_PID ; \
		test -e $CLOUDLAB_TMP_LOG && /bin/rm -f $CLOUDLAB_TMP_LOG ; \
		exit 8' SIGINT SIGTERM

    echo "Trying to acquire lock '$CLOUDLAB_LOCK_NAME'"
	python -m tcpnetlock.client --debug --host=$CLOUDLAB_HOST --port=$CLOUDLAB_PORT --print-marks \
		--client-id=$CLOUDLAB_CLIENT_ID --keep-alive $CLOUDLAB_LOCK_NAME > $CLOUDLAB_TMP_LOG 2>&1 & CLOUDLAB_TMP_PID=$!
	echo "Background PID: $CLOUDLAB_TMP_PID"

	connection_full_line=''
	while [ -z "$connection_full_line" ] ; do
		sleep 0.2  # an initial wait won't hurt
		connection_full_line="$(egrep -o 'MARK,CONNECTION,.+,END' $CLOUDLAB_TMP_LOG)"
	done
	connection=$(echo "$connection_full_line" | cut -d , -f 3)
	case "$connection" in
		"OK") ;;
		"REFUSED"|"REFUSED") echo "Connection to server failed." ; exit $EXIT_CONNECTION_ERROR ;;
		*) echo "Invalid value for CONNECTION: $connection"; exit $EXIT_CONNECTION_INVALID_VALUE ;;
	esac

	acquire_status_full_line=''
	while [ -z "$acquire_status_full_line" ] ; do
		sleep 0.2  # an initial wait won't hurt
		echo "Checking logs..."
		acquire_status_full_line="$(egrep -o 'MARK,LOCK_RESULT,LOCK:.+,ACQUIRED:.+,END' $CLOUDLAB_TMP_LOG)"
	done
	acquired=$(echo "$acquire_status_full_line" | cut -d , -f 4 | cut -d : -f 2)
	case "$acquired" in
		"True") return 0 ;;
		"False") echo "Lock not granted. Exiting." ; exit 7 ;;
		*) echo "Invalid value for acquired: $acquired"; exit 6 ;;
	esac

}

function release_lock() {
    kill $CLOUDLAB_TMP_PID
    rm $CLOUDLAB_TMP_LOG

	trap '' EXIT
	trap '' SIGINT SIGTERM
}
