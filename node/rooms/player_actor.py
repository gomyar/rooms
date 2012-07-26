
import collections

from character_actor import CharacterActor
from actor import expose
from actor import command
from inventory import Inventory
from inventory import create_item
from roll_system import roll

import logging
log = logging.getLogger("rooms.player")


class PlayerActor(CharacterActor):
    def __init__(self, player_id=None, position=(0, 0)):
        super(PlayerActor, self).__init__(player_id, position)
        self.model_type = "investigator"
        self.inventory = Inventory()

    @command()
    def exit(self, player, door_id):
        self.room.exit_through_door(self, door_id)
        self.instance.send_sync(self.actor_id)

    @command()
    def leave_instance(self, player):
        self.instance.deregister(self.actor_id)
