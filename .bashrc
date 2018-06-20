#----------------------------------------------------------------------
#
# Utilities for making development more productive
# Defines a 'tnl' functions for common tasks. Includes autocompletion  ;-)
#
# You SHOULD use 'ondir' or something like that to:
#  1. automatically load virtualenv
#  2. source this script
#
# For example:
#   | $cat ~/.ondirrc 
#   | enter ~/tcpnetlock
#   |   test -e ./venv/bin/activate && source ./venv/bin/activate
#   |   test -e ./.bashrc && source ./.bashrc
#
#----------------------------------------------------------------------

function tnl {
	op=$1
	shift

	case "$op" in
		s|server) python -m tcpnetlock.cli.tnl_server --debug ;; # run the server
		c|client) python -m tcpnetlock.cli.tnl_client --debug test-lock $* ;; # run the client
		d|do) python -m tcpnetlock.cli.tnl_do --debug --lock-name test-lock -- vmstat 5 ;; # run tnl_do
		t|test) py.test -v $* ;;
		l|lint) make lint $* ;;
		tl|test-lint) py.test -v $* && make lint && cowthink ok ;;
		*)
			echo "Invalid: $op"
			echo "Valid options: [s|server] [c|client] [d|do] [t|test] [l|lint] [tl|test-lint] [] [] [] [] [] [] "
			;;
	esac
}

complete -W "server client do test lint test-lint" tnl

