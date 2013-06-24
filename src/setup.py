#!/usr/bin/python

from setuptools import setup, find_packages, findall

setup(name='Rooms',
      version='0.1',
      packages=find_packages(),
      scripts=['bin/rooms'],
      data_files=[
        ('rooms/assets', findall('rooms/assets')),
      ],
)
