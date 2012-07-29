
from scriptutils import load_script
from rooms.npc_actor import NpcActor

from rooms.actor import expose
from rooms.actor import command


def create_npc(area, model, script, room):
    npc = NpcActor(model)
    npc.script = load_script(script)
    area.add_npc(npc, room)
