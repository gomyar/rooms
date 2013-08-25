#!/usr/bin/python

import subprocess
import time
import logging

from rooms.pyclient import RoomsConnection
from test import test


logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

log = logging.getLogger("test")


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

    def start_nodes(self, count):
        # start master
        self._start_master()

        for i in range(count - 1):
            self._start_node(i)

        time.sleep(1)

    def run_test(test_method):
        self.start_nodes(2)

        try:
            test_method()
        except:
            log.exception("Exception running test")
        finally:
            self.stop_nodes()

    def stop_nodes(self):
        for node in self.nodes:
            try:
                node.kill()
            except:
                pass


if __name__ == "__main__":
    run_test(test)
