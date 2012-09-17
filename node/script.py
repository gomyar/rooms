
import eventlet

from scriptutils import load_script
from rooms.npc_actor import NpcActor

from rooms.script import expose
from rooms.script import command
from rooms.script import _actor_info

from rooms.chat import chat as create_chat
from rooms.chat import choice as c
from rooms.chat import call
from rooms.chat import load_chat as load_chat_script


class _NpcStub(object):
    def _npc(self):
        try:
            return _actor_info[eventlet.getcurrent()]
        except:
            import ipdb; ipdb.set_trace()
            raise

    def __getattr__(self, name):
        return getattr(self._npc(), name, None)


npc = _NpcStub()


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


def load_chat(chat_id):
    return load_chat_script(chat_id, npc.script)
