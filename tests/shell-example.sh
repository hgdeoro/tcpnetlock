#!/bin/bash

source $(dirname $0)/../shell/tcpnetlock.sh

lock_in_bg

#
# DO WHAT YOU NEED TO DO HERE
#

for pending in $(seq 5 | tac) ; do
	echo "WORKING... Still $pending pending..."
	sleep 1
done

release_lock

echo "Lock released..."

for pending in $(seq 5 | tac) ; do
	echo "WORKING... Still $pending pending..."
	sleep 1
done

exit 0
