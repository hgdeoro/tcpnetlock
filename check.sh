#!/bin/bash

cd $(dirname $0)

export PYTHONPATH=.

pycodestyle tcpnetlock/

