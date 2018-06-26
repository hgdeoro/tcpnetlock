=======
History
=======

0.1.4 (2018-06-26)
------------------

* Implements retries for cli tnl_do


0.1.3 (2018-06-22)
------------------

* Server logs granted lock
* Add description to CLI
* Client use environment variables for host/port
* Add __str__ to Action to have better logs in server

0.1.2 (2018-06-21)
------------------

* Update client & server to handle errors in a better way
* Add tests
* Update docs

0.1.1 (2018-06-20)
------------------

* Add .bashrc (for developers)
* Fix setup.py

0.1.0 (2018-06-19)
------------------

* Docker start server with --info by default
* Adds cloudbuild.yaml to facilitate building in GCP
* Change in protocol to detect unintended uses
* Detect invalid requests and always send response to client
* BIG refactor of server and client classes
* Add lot of tests (current coverage: 99%)


0.0.8 (2018-06-18)
------------------

* Refactor messy code from server, client and cli


0.0.7 (2018-06-17)
------------------

* Code cleanup and refactor
* Add tests
* Implements run_with_lock script to make really easy to use from shell scripts

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
