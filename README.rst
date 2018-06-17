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
