.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/hgdeoro/tcpnetlock/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

TcpNetLock could always use more documentation, whether as part of the
official TcpNetLock docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/hgdeoro/tcpnetlock/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `tcpnetlock` for local development.

1. Fork the `tcpnetlock` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/tcpnetlock.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv tcpnetlock
    $ cd tcpnetlock/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 tcpnetlock tests
    $ python setup.py test or py.test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 2.7, 3.4, 3.5 and 3.6, and for PyPy. Check
   https://travis-ci.org/hgdeoro/tcpnetlock/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

    $ py.test tests


Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).

Then, to test & bump version run::

    $ ( make clean ; \
        test -z "$(git status --porcelain)" || { echo "WORKING DIRECTORY IS NOT CLEAN" ; exit 1 ; } && \
        tox && \
        bumpversion patch && \
        echo "ENTER to continue..." && \
        read && \
        git push && \
        git push --tags )

To upload to test.pypi.org::

    $ ( make clean ; \
        python3 setup.py sdist bdist_wheel ; \
        twine upload -r pypitest dist/* ; \
        VERSION=$(python setup.py --version) ; \
        deactivate ; \
        cd / ; \
        export VID=$(uuidgen) ; \
        virtualenv -p python3.6 /tmp/venv-$VID ; \
        source /tmp/venv-$VID/bin/activate ; \
        pip install --index-url https://test.pypi.org/simple/ tcpnetlock==${VERSION}; \
        )

To upload to pypi.org::

    $ twine upload -r pypi dist/*


To install locally in a brand new virtualenv::

    $ ( make clean ; \
        python3 setup.py sdist bdist_wheel ; \
        deactivate ; \
        export VID=$(uuidgen) ; \
        virtualenv -p python3.6 /tmp/venv-$VID ; \
        source /tmp/venv-$VID/bin/activate ; \
        pip install ./dist/tcpnetlock*.whl ; \
        )

To build the Docker image::

    $ ( VERSION=$(python setup.py --version) ; \
        docker build --build-arg TNS_VERSION=v${VERSION} \
            -f docker/Dockerfile docker/ \
            -t hgdeoro/tcpnetlock:v${VERSION} \
            -t hgdeoro/tcpnetlock:latest ; \
        docker push hgdeoro/tcpnetlock ;\
        )

To generate the commands required to build docker in a remote server (for faster upload of image)::

    $ ( VERSION=$(python setup.py --version) ; \
        echo git clone --depth 1 --single-branch --branch v${VERSION}  https://github.com/hgdeoro/tcpnetlock.git '&& \'; \
        echo cd tcpnetlock '&& \' ; \
        echo docker build --build-arg TNS_VERSION=v${VERSION} \
            -f docker/Dockerfile docker/ \
            -t hgdeoro/tcpnetlock:v${VERSION} \
            -t hgdeoro/tcpnetlock:latest '&& \' ; \
        echo docker push hgdeoro/tcpnetlock '&& \' ; \
        echo docker run --rm -ti hgdeoro/tcpnetlock:v${VERSION}
        )
