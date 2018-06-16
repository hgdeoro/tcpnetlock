#!/bin/bash

PORT=${PORT:-34567}
CLIENT_ID=$(uuidgen)
LOCK_NAME=lock-image-thumbnail-generator
LOG=$(mktemp)

echo "Logging to $LOG"
trap 'echo "Cleanup pids $pids and $LOG" ; ps --no-headers -q $pids | grep -q $pids && kill $pids ; test -e $LOG && /bin/rm -f $LOG' EXIT
trap 'echo "Cleanup pids $pids and $LOG" ; ps --no-headers -q $pids | grep -q $pids && kill $pids ; test -e $LOG && /bin/rm -f $LOG ; exit 8' SIGINT SIGTERM

python -m tcpnetlock.client --debug --port=$PORT --client-id=$CLIENT_ID --keep-alive $LOCK_NAME > $LOG 2>&1 & pids=$!
echo "Background PIDs: $pids"

full_status=''
while [ -z "$full_status" ] ; do
	sleep 0.2  # an initial wait won't hurt
	echo "Checking logs..."
	full_status="$(egrep -o 'LOCK_RESULT,LOCK:.+,ACQUIRED:.+' $LOG)"
done

acquired=$(echo "$full_status" | cut -d , -f 3 | cut -d : -f 2)
case "$acquired" in
	"True") ;;
	"False") echo "Lock not granted. Exiting." ; exit 7 ;;
	*) echo "Invalid value for acquired: $acquired"; exit 6 ;;
esac

#
# DO WHAT YOU NEED TO DO HERE
#

for pending in $(seq 3 | tac) ; do
	echo "WORKING... Still $pending pending..."
	sleep 1
done

exit 0
