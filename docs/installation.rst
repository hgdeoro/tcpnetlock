.. highlight:: shell

============
Installation
============


Stable release
--------------

To install TcpNetLock, run this command in your terminal:

.. code-block:: console

    $ pip install tcpnetlock

This is the preferred method to install TcpNetLock, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


Docker image
------------

To run it using Docker, get the image::

    $ docker image pull hgdeoro/tcpnetlock


And then launch a container::

    $ docker run --rm -ti -p 7654:7654 hgdeoro/tcpnetlock


From sources
------------

The sources for TcpNetLock can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/hgdeoro/tcpnetlock

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/hgdeoro/tcpnetlock/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/hgdeoro/tcpnetlock
.. _tarball: https://github.com/hgdeoro/tcpnetlock/tarball/master
