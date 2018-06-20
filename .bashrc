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

function _tnl_assert_clean {
        test -z "$(git status --porcelain)" || { cowthink "ERROR: WORKING DIRECTORY IS NOT CLEAN" ; return 1 ; }
}

function _tnl_test_installed {
	tcpnetlock_server --debug &
	sleep 1
	tcpnetlock_do --debug --lock-name lock1 -- vmstat 1 1
	kill %1
}

function _tnl_pre_release {
(
	set -e
	trap 'cowthink ooooops' ERR
	set -x
	_tnl_assert_clean
	make clean
	tox
	# make coverage <- avoid html report
	coverage run --branch --source tcpnetlock -m pytest
	coverage report -m
	make dist
	(
		ORIGDIR=$(pwd)
		deactivate
		cd /
		export VID=$(uuidgen)
		virtualenv -p python3.6 /tmp/venv-$VID
		source /tmp/venv-$VID/bin/activate
		pip install ${ORIGDIR}/dist/tcpnetlock-*.tar.gz

		_tnl_test_installed
		cowthink ok
	)
)
}

function _tnl_release {
(
	# Assuming you already ran 'pre-release'
	set -e
	trap 'cowthink ooooops' ERR
	set -x
	_tnl_assert_clean
	bumpversion ${TNL_BUMP:-patch}
	make clean dist
	VERSION=$(python setup.py --version)
	twine upload -r pypitest dist/*
	(
		deactivate
		cd /
		export VID=$(uuidgen)
		virtualenv -p python3.6 /tmp/venv-$VID
		source /tmp/venv-$VID/bin/activate
		pip install --index-url https://test.pypi.org/simple/ tcpnetlock==${VERSION};

		_tnl_test_installed
		cowthink ok
	)
)
}

function _tnl_upload {
(
	# Assuming you already ran 'release'
	_tnl_assert_clean
	git push
	git push --tags
	twine upload -r pypi dist/*
)
}



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
		g|coverage) make coverage $* ;;
		pre-release) _tnl_pre_release ;;
		release) _tnl_release ;;
		upload) _tnl_upload ;;
		*)
			echo "Invalid: $op"
			echo "Valid options: [s|server] [c|client] [d|do] [t|test] [l|lint] [tl|test-lint] [g|coverage] [pre-release]"
			;;
	esac
}

# 'release' and 'upload' are NOT autocompleted to avoid potential erroneous execution
complete -W "server client do test lint test-lint coverage pre-release" tnl
