
import collections
import time

from actor import Actor
from roll_system import roll
from rooms.null import Null

import logging
log = logging.getLogger("rooms.player")


class PlayerActor(Actor):
    def __init__(self, player, actor_id=None):
        super(PlayerActor, self).__init__(actor_id)
        self.player = player
        self.server = Null()
        self.actor_type = "player"

    def __repr__(self):
        return "<PlayerActor %s:%s>" % (self.player.username, self.actor_id)

    def exit(self, door_id):
        super(PlayerActor, self).exit(door_id)
        self.player.room_id = self.room.room_id
        self.server.send_sync(self.player.username)

    def leave_game(self):
        self.server.deregister(self.actor_id)

    def add_log(self, msg, *args):
        log_entry = { 'msg': msg % args, 'time': time.time() }
        self.log.append(log_entry)
        if len(self.log) > 50:
            self.log.pop(0)
        self.send_update("log", **log_entry)

    def add_chat_message(self, msg, *args):
        self.add_log(msg, *args)

    def send_update(self, update_id, **kwargs):
        self.server.send_update(self.player.username, update_id, **kwargs)

    def _update(self, update_id, **kwargs):
        self.send_update(update_id, **kwargs)

    def actor_updated(self, actor):
        log.debug("update....")
        self.server.send_update(self.player.username, "actor_update",
            **actor.external())

    def actor_added(self, actor):
        self.server.send_update(self.player.username, "actor_update",
            **actor.external())

    def send_actor_update(self):
        super(PlayerActor, self).send_actor_update()
        self.server.send_update(self.player.username, "actor_update",
            **self.internal())

    def actor_removed(self, actor):
        log.debug(" --- actor removed: %s", actor)
        self.server.send_update(self.player.username, "remove_actor",
            actor_id=actor.actor_id)

    def actor_heard(self, actor, message):
        msg = "You say :" if self == actor else "%s says :" % (actor.actor_id,)
        self.send_update("actor_heard", actor_id=actor.actor_id, msg=message)

    def kill(self):
        self.server.node.kill_player(self)
        super(PlayerActor, self).kill()
