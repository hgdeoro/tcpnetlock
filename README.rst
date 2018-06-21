==========
TcpNetLock
==========


.. image:: https://img.shields.io/pypi/v/tcpnetlock.svg
        :target: https://pypi.python.org/pypi/tcpnetlock

.. image:: https://img.shields.io/travis/hgdeoro/tcpnetlock.svg
        :target: https://travis-ci.org/hgdeoro/tcpnetlock

.. image:: https://readthedocs.org/projects/tcpnetlock/badge/?version=latest
        :target: https://tcpnetlock.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/hgdeoro/tcpnetlock/shield.svg
     :target: https://pyup.io/repos/github/hgdeoro/tcpnetlock/
     :alt: Updates



Network lock based on TCP sockets


* Free software: GNU General Public License v3
* Documentation: https://tcpnetlock.readthedocs.io.


Why?
----

While deploying applications to Kubernetes, I needed a way to make sure that
some potential concurrent, distributed actions, are not executed concurrently.
For example:

 * database migrations: just one Pod in the Kubernetes cluster should be able to apply the database migrations
 * for batch jobs, different workers could be working on the same resource, this can be avoided with this lock mechanism

Of course, Zookeeper is a MUCH BETTER solution, but that's too much for my use cases...

How it works
------------

Assuming the server is running on localhost, let's get a lock using telnet::

    $ telnet localhost 7654
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.

To try to acquire a lock, send::

    lock,name:django-migrations

Server responds with::

    ok

From that point, and while the TCP connection is open, you have the lock.

If you try the same in a different terminal, you will get::

    $ telnet localhost 7654
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.
    lock,name:django-migrations        <= you write
    not-granted                        <= server response
    Connection closed by foreign host. <= server closed the connection

Here the server responded with **not-granted** and closed the TCP connection. The lock was not granted to you.

But, in real-life scenarios, you would use the provided utility **tcpnetlock_do**::

    $ tcpnetlock_do --lock-name django-migrations -- python manage.py migrate

To test it, you will need the server running. To get the server running with Docker, just run::

    $ docker pull hgdeoro/tcpnetlock
    $ docker run -ti --rm -p 7654:7654 hgdeoro/tcpnetlock

Alternatively, you can install the package in a virtualenv and launch the server::

    $ virtualenv -p python3.6 venv
    $ source venv/bin/activate
    $ pip install tcpnetlock
    $ tcpnetlock_server --info
    INFO:root:Started server listening on localhost:7654


Features
--------

* Runs on Python 3.6 / Python 3.5
* Do not require external libraries
* Ready to use Docker image (based on Alpine)
* Includes server and python client
* Includes utility to run Linux commands while holding the lock
* Simple protocol: you can get a lock even with `nc`

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
