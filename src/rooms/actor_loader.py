
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
        for ((game_id, room_id), room) in self.node.rooms.items():
            actor = self.node.container.load_limbo_actor(game_id, room_id)
            if actor:
                log.debug("Loaded actor %s into room %s", actor, room_id)
                if actor.actor_id not in room.actors:
                    docked = self.node.container.load_docked_actors(game_id,
                        actor.actor_id)
                    log.debug("Loaded docked: %s", docked)
                    room.put_actor(actor)
                    for child in docked:
                        room.put_actor(child)
        Timer.sleep(0.1)
