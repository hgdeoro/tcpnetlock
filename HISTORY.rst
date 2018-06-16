=======
History
=======

0.0.6 (2018-06-16)
------------------

* Create shell script to be sourced, to facilitate use of tcpnetlock from shell scripts

0.0.5 (2018-06-15)
------------------

* Update CONTRIBUTING (documents commands for the full release process)
* Disable upload to pypi from Travis-CI

0.0.4 (2018-06-15)
------------------

* Encapsulate Lock, adds client id and timestamp
* Implement sending of keepalive from client
* Remove use of 'click'
* Start server from cli with configurable parameters (listen address, port, etc)
* Use client id to identify who has the lock

0.0.3 (2018-06-15)
------------------

* Validate lock name in server
* FIX client to handle RESPONSE_ERR response
* Add unittests
* Refactor locks into server class
* Use threading for test server
* Make code compatible with Python 3.5

0.0.2 (2018-06-15)
------------------

* Implements RELEASE of locks
* FIX release of lock when client closes the connection
* Validates lock name
* Code refactoring

0.0.1 (2018-06-15)
------------------

* Add files from cookiecutter-pypackage
* Migrate test cases to pytest
