
import gevent
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.actorloader")


class RoomLoader(object):
    def __init__(self, node):
        self.node = node
        self.running = False
        self._gthread = None

    def start(self):
        self.running = True
        self._gthread = gevent.spawn(self.load_loop)

    def stop(self):
        self.running = False
        if self._gthread:
            self._gthread.join()

    def load_loop(self):
        while self.running:
            self._load_rooms()
            Timer.sleep(1)

    def _load_rooms(self):
        self.node.load_next_pending_room()
