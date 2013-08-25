
import time
import gevent
import subprocess
import os

from rooms.pyclient import RoomsConnection


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
        self.master = subprocess.Popen(["/usr/local/bin/rooms",
            "-c", "localhost:9000",
            "-i", "localhost:9001",
            "-a", "localhost:9002",
            "-g", self.game_dir()])

    def _start_node(self, offset):
        self.nodes.append(subprocess.Popen(["/usr/local/bin/rooms",
            "-c", "localhost:9000",
            "-i", "localhost:7%03d" % (offset + 80,),
            "-a", "localhost:8%03d" % (offset + 80,),
            "-g", self.game_dir(),
            "-j"]))

    def start_game(self, node_count=1):
        # start master
        self._start_master()

        for i in range(node_count - 1):
            self._start_node(i)

        time.sleep(1)

    def stop_game(self):
        try:
            self.master.kill()
        except:
            pass
        for node in self.nodes:
            try:
                node.kill()
            except:
                pass


def open_connection():
    return RoomsConnection("localhost", 9000)

