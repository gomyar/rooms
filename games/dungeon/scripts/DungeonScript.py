
import uuid

from scriptutils import load_script
from script import *

from room import Room

from npc_actor import NpcActor
from item_actor import ItemActor
import OrcScript
import player_script


class DungeonScript(Script):
    def player_joined_instance(self, player):
        player.script = player_script
        player.stats['hp'] = 10

    def player_enters_room(self, room, player):
        orc = NpcActor(str(uuid.uuid1()), OrcScript)
        orc.model_type = "orc"
        room.add_npc(orc, room.center())
        orc.kickoff()

        item = ItemActor(str(uuid.uuid1()))
        item.model_type = "gold"
        room.add_npc(item, room.center())
