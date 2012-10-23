
import uuid

from rooms.npc_actor import NpcActor
from rooms.item_actor import ItemActor


def create_npc(area, actor_id, model, script, room_id):
    npc = NpcActor(actor_id)
    npc.model_type = model
    npc.load_script(script)
    area.add_npc(npc, room)

def create_item(area, item_type, room_id, position=None):
    item = ItemActor(str(uuid.uuid1()))
    item.load_script("item_script")
    item.model_type = item_type
    area[room].add_item(item, position)
