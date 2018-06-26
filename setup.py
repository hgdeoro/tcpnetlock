#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Horacio G. de Oro",
    author_email='hgdeoro@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    description="Network lock based on TCP sockets",
    entry_points={
        'console_scripts': [
            'tcpnetlock_server=tcpnetlock.cli.tnl_server:main',
            'tcpnetlock_client=tcpnetlock.cli.tnl_client:main',
            'tcpnetlock_do=tcpnetlock.cli.tnl_do:main'
        ],
    },
    scripts=[],
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='tcpnetlock',
    name='tcpnetlock',
    packages=find_packages(include=[
        'tcpnetlock',
        'tcpnetlock.client',
        'tcpnetlock.cli',
        'tcpnetlock.server',
    ]),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/hgdeoro/tcpnetlock',
    version='0.1.5',
    zip_safe=False,
)
