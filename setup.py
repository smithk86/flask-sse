#!/usr/bin/env python

from setuptools import setup

setup(
    name='flask-sse',
    version='0.1',
    packages=['flask_sse'],
    install_requires=[
        'flask',
        'gevent'
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest',
        'pytest-flask',
        'pytest-flask-gevent-wsgiserver'
    ],
    classifiers=[
        'Framework :: Flask',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
