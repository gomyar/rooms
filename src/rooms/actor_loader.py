
import gevent
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.actorloader")


class ActorLoader(object):
    def __init__(self, room):
        self.room = room
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
            self._load_actors()
            Timer.sleep(1)

    def _load_actors(self):
        game_id = self.room.game_id
        room_id = self.room.room_id
        actor = self.room.node.container.load_limbo_actor(game_id, room_id)
        if actor:
            log.debug("Loaded actor %s into room %s", actor, room_id)
            self.process_actor(actor)

    def process_actor(self, actor):
        docked = self._load_docked(actor.game_id, actor)
        self.room.put_actor(actor)
        for child in docked:
            self.room.put_actor(child)
            self._check_is_player_added(child)
        if not actor.initialized:
            actor.script_call("created")
            actor.initialized = True
            self.room.node.container.save_actor(actor)
        self._check_is_player_added(actor)

    def _check_is_player_added(self, actor):
        if actor.is_player:
            actor.room.node.players[actor.game_id, actor.username] = (
                actor.room.room_id, actor.actor_id)
            log.debug("Added player %s, %s as %s, %s at %s",
                actor.game_id, actor.username, actor.room.room_id, actor.actor_id, actor.position)

    def _load_docked(self, game_id, actor):
        docked = self.room.node.container.load_docked_actors(game_id,
            actor.actor_id)
        for child in list(docked):
            docked.extend(self._load_docked(game_id, child))
        return docked
