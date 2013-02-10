
from functools import wraps
import inspect

from rooms.chat import chat as create_chat
from rooms.chat import choice as c
from rooms.chat import call
from rooms.chat import load_chat as load_chat_script
from rooms.waypoint import get_now

from scriptutils import create_npc
from scriptutils import create_item

import logging
log = logging.getLogger('rooms.script')


def command(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_command = True
    wrapped.args = inspect.getargspec(func).args
    return wrapped


def request(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_request = True
    wrapped.args = inspect.getargspec(func).args
    return wrapped


def conversation(func):
    @wraps(func)
    def wrapped(npc, player, message=None):
        if message:
            return npc.chat(player, message)
        else:
            npc.create_chat(player, func(npc, player))
            return npc.chat(player)
    wrapped.is_request = True
    return wrapped


def chat_delay(actor):
    actor.sleep(10)

def move_to_object(actor, object_id):
    actor.move_to(*actor.room.map_objects[object_id].position)

def load_chat(chat_script, npc):
    return load_chat_script(chat_script, npc.script, npc)
