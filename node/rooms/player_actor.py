
import collections
import time

from character_actor import CharacterActor
from actor import expose
from actor import command
from inventory import Inventory
from inventory import create_item
from roll_system import roll

import logging
log = logging.getLogger("rooms.player")


class PlayerActor(CharacterActor):
    def __init__(self, player_id=None, position=(0, 0), instance=None):
        super(PlayerActor, self).__init__(player_id, position)
        self.model_type = "investigator"
        self.inventory = Inventory()
        self.instance = instance

    @command()
    def exit(self, door_id):
        self.room.exit_through_door(self, door_id)
        self.instance.send_sync(self.actor_id)

    @command()
    def leave_instance(self):
        self.instance.deregister(self.actor_id)

    def add_log(self, msg, *args):
        log_entry = { 'msg': msg % args, 'time': time.time() }
        self.log.append(log_entry)
        self.send_event("log", **log_entry)

    def add_chat_message(self, msg, *args):
        self.add_log(msg, *args)

    def send_event(self, event_id, **kwargs):
        self.instance.send_event(self.actor_id, event_id, **kwargs)

    def event(self, event_id, **kwargs):
        self.send_event(event_id, **kwargs)
