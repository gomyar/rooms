#!/usr/bin/python

import subprocess
import time
import logging

logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

log = logging.getLogger("test")


from rooms.pyclient import RoomsConnection
from test import test

# start master
proc1 = subprocess.Popen(["/usr/local/bin/rooms", "-c", "localhost:8082",
    "-i", "localhost:9991", "-a", "localhost:8080",
    "-g", "/home/ray/projects/rooms/ats/test_game_1/"])
print "Started master pid: %s" % (proc1.pid,)

time.sleep(1)
print "Master started"

# start node, join cluster
proc2 = subprocess.Popen(["/usr/local/bin/rooms" ,"-c", "localhost:8082",
    "-i", "localhost:9992", "-a", "localhost:8081",
    "-g", "/home/ray/projects/rooms/ats/test_game_1/", "-j"])
print "Started node pid: %s" % (proc2.pid,)

time.sleep(1)
print "Node started"

try:
    test()

except:
    log.exception("Exception running test")

finally:
    try:
        proc2.kill()
        print "Killed node"
    except:
        pass

    try:
        proc1.kill()
        print "Killed master"
    except:
        pass

