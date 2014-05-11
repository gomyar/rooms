#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name='Rooms',
    version='0.1',
    description='Networked Game Engine.',
    packages=find_packages("src"),
    include_package_data=True,
    package_dir= { '': 'src'},
    install_requires=['gevent', 'gevent-websocket', 'ws4py', 'pymongo'],
    scripts=['bin/rooms_node', 'bin/rooms_master'],
)
