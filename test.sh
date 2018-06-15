#!/bin/bash

cd $(dirname $0)

export PYTHONPATH=.

python -m tcpnetlock.test $*
