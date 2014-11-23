
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.actorloader")


class ActorLoader(object):
    def __init__(self, node):
        self.node = node

    def load_loop(self):
        while True:
            self._load_actors()

    def _load_actors(self):
        for room_id, room in self.node.rooms.items():
            actors = self.node.container.load_limbo_actors(room_id)
            for actor in actors:
                log.debug("Loaded actor %s into room %s", actor, room_id)
                room.put_actor(actor)
            Timer.sleep(0.1)
        Timer.sleep(0.1)
