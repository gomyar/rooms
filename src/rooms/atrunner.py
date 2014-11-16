
import os
import time
import subprocess
import atexit
import gevent
from rooms.pyclient import RoomsConnection
import logging
log = logging.getLogger("rooms.atrunner")


class RoomsTestRunner(object):
    def __init__(self, test_script_path, game_dir_path):
        self.test_script_path = test_script_path
        self.game_dir_path = game_dir_path
        self.nodes = []
        self.master = None

    def game_dir(self):
        root_dir = os.path.realpath(os.path.dirname(self.test_script_path))
        return os.path.join(root_dir, self.game_dir_path)

    def _start_master(self):
        self.master = subprocess.Popen(["rooms_master",
            "-a", "localhost:9000",
            "-g", self.game_dir()])
        atexit.register(self.master.terminate)
        time.sleep(0.5)

    def _start_node(self, offset):
        node = subprocess.Popen(["rooms_node",
            "-a", "localhost:8%03d" % (offset,),
            "-m", "localhost:9000",
            "-g", self.game_dir()])
        atexit.register(node.terminate)
        self.nodes.append(node)

    def start_service(self, count):
        # start master
        self._start_master()

        for i in range(count - 1):
            self._start_node(i)

        time.sleep(1)

    def run_test(test_method):
        self.start_service(2)

        try:
            test_method()
        except:
            log.exception("Exception running test")
        finally:
            self.stop_nodes()

    def stop_service(self):
        for node in self.nodes:
            try:
                node.kill()
            except:
                pass


def wait_for_sync(conn, timeout=1):
    now = time.time()
    while not conn.player_actor and time.time() < now + timeout:
        gevent.sleep(0.1)
    if not conn.player_actor:
        raise AssertionError("No sync occured after %s seconds" % (timeout,))


def wait_for_state(actor, state, value, timeout=1):
    now = time.time()
    while actor.state.get(state) != value and time.time() < now + timeout:
        gevent.sleep(0.1)
    if actor.state.get(state) != value:
        raise AssertionError("Actor %s state does not match: %s != %s" % (
            actor, actor.state.get(state), value))


def wait_for_position(actor, position, timeout=1):
    now = time.time()
    while actor.position() != position and time.time() < now + timeout:
        gevent.sleep(0.1)
    if actor.position() != position:
        raise AssertionError("Actor %s position does not match: %s != %s" % (
            actor, actor.position(), position))
