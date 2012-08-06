
from scriptutils import load_script
from rooms.npc_actor import NpcActor

from rooms.actor import expose
from rooms.actor import command


def create_npc(area, actor_id, model, script, room):
    npc = NpcActor(actor_id)
    npc.model_type = model
    npc.load_script(script)
    area.add_npc(npc, room)
