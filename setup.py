#!/usr/bin/python

from setuptools import setup, find_packages

requirements = open("requirements.txt")

setup(
    name='Rooms',
    version='0.1',
    description='Networked Game Engine.',
    packages=find_packages("src"),
    include_package_data=True,
    package_dir= { '': 'src'},
    install_requires=[req.strip() for req in requirements],
    scripts=['bin/rooms_node', 'bin/rooms_master'],
)
