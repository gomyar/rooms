
import collections

from character_actor import CharacterActor
from actor import expose
from actor import command
from inventory import Inventory
from inventory import create_item
from roll_system import roll

import logging
log = logging.getLogger("rooms.player")


class PlayerKnowledge(dict):
    def __getattr__(self, name):
        return self.__getitem__(name) if name in self else ""

    def __setattr__(self, name, value):
        self.__setitem__(name, value)


class PlayerActor(CharacterActor):
    def __init__(self, player_id=None, position=(0, 0)):
        super(PlayerActor, self).__init__(player_id, position)
        self.model_type = "investigator"
        self.inventory = Inventory()
        self.data = PlayerKnowledge()

    def set_path(self, path):
        super(PlayerActor, self).set_path(path)
        for point in path:
            for actor in self.room.all_npcs():
                if actor.distance_to(point) < 100:
                    actor.event("player_moved_nearby", self)

    def external(self):
        ex = super(PlayerActor, self).external()
        ex['model_type'] = self.model_type
        return ex

    @command()
    def walk_to(self, x, y):
        return super(PlayerActor, self).walk_to(x, y)

    @command()
    def exit(self, door_id):
        self.room.exit_through_door(self, door_id)
        self.instance.send_sync(self.actor_id)

    @command()
    def leave_instance(self):
        self.instance.deregister(self.actor_id)

    @command()
    def list_inventory(self):
        return self.inventory.all_items()

    def add_evidence(self, npc, category, description):
        evidence = create_item(npc_id=npc.actor_id, category=category,
            description=description)
        self.inventory.add_item(evidence)
        self.add_chat_message("You learned something about %s: %s" % (
            npc.actor_id, description))

    def has_evidence(self, npc, category):
        return self.inventory.find_items(npc_id=npc.actor_id,
            category=category)

    def attack(self, actor):
        log.info("%s attacking %s", actor.actor_id, self.actor_id)
        target_actor = self.room.actors[actor.actor_id]
        if roll(self, ["str", "brawl"], 10):
            self.perform_action("melee_attack", 1, hp=5)
        else:
            self.perform_action("melee_attack_missed", 1)
