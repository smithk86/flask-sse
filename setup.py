#!/usr/bin/env python

from setuptools import setup

setup(
    name='flask-sse',
    version='0.1',
    license='MIT',
    author='Kyle Smith',
    author_email='smithk86@gmail.com',
    description='flask plugin to facilitate server-sent events',
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
        'pytest-flask-gevent-wsgiserver',
        'requests'
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
