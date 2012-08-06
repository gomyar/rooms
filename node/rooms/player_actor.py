
import collections
import time

from actor import Actor
from inventory import Inventory
from inventory import create_item
from roll_system import roll

import logging
log = logging.getLogger("rooms.player")


class PlayerActor(Actor):
    def __init__(self, player_id=None, position=(0, 0), instance=None):
        super(PlayerActor, self).__init__(player_id, position)
        self.model_type = "investigator"
        self.inventory = Inventory()

    def exit(self, door_id):
        self.room.exit_through_door(self, door_id)
        self.instance.send_sync(self.actor_id)

    def leave_instance(self):
        self.instance.deregister(self.actor_id)

    def add_log(self, msg, *args):
        log_entry = { 'msg': msg % args, 'time': time.time() }
        self.log.append(log_entry)
        self.send_update("log", **log_entry)

    def add_chat_message(self, msg, *args):
        self.add_log(msg, *args)

    def send_update(self, event_id, **kwargs):
        self.instance.send_update(self.actor_id, event_id, **kwargs)

    def process_actor_update(self, actor_state):
        self.send_update("actor_update", **actor_state)

    def actor_exited_room(self, actor, door_id):
        self.send_update("actor_exited_room", actor_id=actor.actor_id)

    def actor_entered_room(self, actor, door_id):
        self.send_update("actor_entered_room", **actor.external(self))
