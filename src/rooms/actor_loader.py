
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.actorloader")


class ActorLoader(object):
    def __init__(self, room):
        self.room = room
        self.running = False

    def load_loop(self):
        self.running = True
        while self.running:
            self._load_actors()
            Timer.sleep(1)

    def _load_actors(self):
        game_id = self.room.game_id
        room_id = self.room.room_id
        actor = self.room.node.container.load_limbo_actor(game_id, room_id)
        if actor:
            log.debug("Loaded actor %s into room %s", actor, room_id)
            if actor.actor_id not in self.room.actors:
                docked = self._load_docked(game_id, actor)
                log.debug("Loaded docked: %s", docked)
                self.room.put_actor(actor)
                for child in docked:
                    self.room.put_actor(child)
            else:
                raise Exception('Actor %s,%s already loaded' % (game_id, room_id))

    def _load_docked(self, game_id, actor):
        docked = self.room.node.container.load_docked_actors(game_id,
            actor.actor_id)
        for child in list(docked):
            docked.extend(self._load_docked(game_id, child))
        return docked
