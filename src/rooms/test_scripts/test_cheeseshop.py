
import yaml
import os

from rooms.basicchat import Chat

path = os.path.join(os.path.dirname(__file__), "cheeseshop.yaml")
chat = Chat("cheeseshop_chat", yaml.load(open(path)))


def ping(actor, player, msg):
    return "pong: %s" % (msg,)


def say(actor, player, msg):
    return chat['conversations'][msg or 'default']


def start_conversation(actor, player):
    response = chat.start_conversation(player, actor)
    return _response_view(response)


def chat_response(actor, player, choice_index):
    response = chat.respond(player, actor, choice_index)
    return _response_view(response)


def _response_view(response):
    if response:
        return {'msg': response['msg'],
            'choices': [(index, choice['say']) for (index, choice) in \
                response['choices']]}
    else:
        return {}
