#!/usr/bin/python

import subprocess
import time
import logging

from rooms.pyclient import RoomsConnection
from test import test


logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

log = logging.getLogger("test")



if __name__ == "__main__":
    run_test(test)
