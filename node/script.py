
from functools import wraps
import eventlet

from rooms.chat import chat as create_chat
from rooms.chat import choice as c
from rooms.chat import call

from scriptutils import create_npc

import logging
log = logging.getLogger('rooms.script')


def expose(func=None, **filters):
    if func==None:
        def inner(func):
            return expose(func, **filters)
        return inner
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_exposed = True
    wrapped.filters = filters
    return wrapped


def command(func=None, **filters):
    if func==None:
        def inner(func):
            return command(func, **filters)
        return inner
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_command = True
    wrapped.filters = filters
    return wrapped


def request(func=None, **filters):
    if func==None:
        def inner(func):
            return command(func, **filters)
        return inner
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_command = True
    wrapped.is_request = True
    wrapped.filters = filters
    return wrapped


def conversation(func=None):
    @wraps(func)
    def wrapped(npc, player, message=None):
        if message:
            return npc.chat(player, message)
        else:
            npc.create_chat(player, func(npc, player))
            return npc.chat(player)
    wrapped.is_exposed = True
    wrapped.filters = None
    wrapped.is_request = True
    return wrapped


def chat_delay(actor):
    eventlet.sleep(10)

def kick(actor):
    pass

def move_to_object(actor, object_id):
    actor.move_to(*actor.room.map_objects[object_id].position)
