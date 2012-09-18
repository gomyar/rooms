
import eventlet

from scriptutils import load_script
from rooms.npc_actor import NpcActor

from rooms.script import expose
from rooms.script import command
from rooms.script import _actor_info

from rooms.chat import chat as create_chat
from rooms.chat import choice as c
from rooms.chat import call


def conversation(func=None):
    def wrapped(npc, player, message=None):
        if message:
            return npc.chat(player, message)
        else:
            npc.create_chat(player, func(npc, player))
            return npc.chat(player)
    wrapped.is_exposed = True
    wrapped.filters = None
    return wrapped


def create_npc(area, actor_id, model, script, room):
    npc = NpcActor(actor_id)
    npc.model_type = model
    npc.load_script(script)
    area.add_npc(npc, room)

