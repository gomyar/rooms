#!/usr/bin/python

import subprocess
import time
import logging

logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

log = logging.getLogger("test")


from rooms.pyclient import RoomsConnection

# start master
proc1 = subprocess.Popen(["/usr/local/bin/rooms", "-c", "localhost:8082",
    "-i", "localhost:9991", "-a", "localhost:8080",
    "-g", "/home/ray/projects/rooms/ats/test_game_1/"])
print "Started master pid: %s" % (proc1.pid,)

time.sleep(1)
print "Rooms started"

try:
    conn = RoomsConnection("localhost", 8082)

    conn.create_game(owner_username="bob", game_id="735700000000000000000000")

    print "Getting info"
    info = conn.player_info("bob", "735700000000000000000000")
    print info
    if not info:
        print "Joining game"
        conn.join_game("bob", "735700000000000000000000", "area1", "room1",
            start_state="some value")
    else:
        print "Connecting to game"
        conn.connect_to_game("bob", "735700000000000000000000")


    admin_conn = RoomsConnection("localhost", 8082)

    admin_conn.admin_connect("ray", "area1", "room1")

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

