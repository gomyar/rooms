
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.actorloader")


class RoomLoader(object):
    def __init__(self, node):
        self.node = node
        self.running = False

    def load_loop(self):
        self.running = True
        while self.running:
            self._load_rooms()
            Timer.sleep(1)

    def _load_rooms(self):
        self.node.load_next_pending_room()
