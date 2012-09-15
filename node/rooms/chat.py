
import os

import simplejson
from rooms.settings import settings


class Conversation:
    def __init__(self, choices=None):
        self.choices = choices or []
        self.current_choice = self
        for choice in self.choices:
            choice.set_parent(self)

    def said(self, message):
        for choice in self.current_choice.choices:
            if choice.matches(message):
                return choice.respond()
        return None

    def reset(self):
        self.current_choice = self

    def choice_list(self):
        return [str(choice.query_text) for choice in \
            self.current_choice.choices]

    def add(self, choice):
        self.choices.append(choice)
        choice.parent = self
        for c in choice.choices:
            c.set_parent(self)


class RespondChoice:
    def __init__(self, query_text, response, choices=None):
        self.query_text = query_text
        self.response = response
        self.choices = choices or []
        self.parent = None

    def __repr__(self):
        return "<Choice %s %s %s>" % (self.query_text[:10] + '...',
            self.response[:10] + '...', self.choices)

    def set_parent(self, parent):
        self.parent = parent
        for choice in self.choices:
            choice.set_parent(parent)

    def respond(self):
        if type(self.response) is str:
            self.parent.current_choice = self
            return self.response
        elif callable(self.response):
            self.parent.current_choice = self
            self.response()
            return ""

    def matches(self, query_text):
        return query_text == self.query_text

class Call(object):
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        return self._func(*self._args, **self._kwargs)

    def set_parent(self, parent):
        pass

def choice(query_text, response, *choices):
    return RespondChoice(query_text, response, choices)

def chat(*choices):
    return Conversation(list(choices))

def call(func, *args, **kwargs):
    return Call(func, *args, **kwargs)

def _read_choice(choice_json, script):
    if 'run_function' in choice_json:
        return Call(getattr(script, choice_json['run_function']))
    else:
        choice = RespondChoice(choice_json.get('request', ''),
            choice_json.get('response', ''))
        for inner in choice_json.get('choices', []):
            choice.choices.append(_read_choice(inner, script))
        return choice

def _check_show_function(choice, script):
    return 'show_function' not in choice or \
        getattr(script, choice['show_function'])()

def load_chat(chat_id, script):
    chat_json = simplejson.loads(open(os.path.join(
        settings.get("script_dir", ""), chat_id + ".json")).read())
    conversation = Conversation()
    for choice in chat_json.get('choices', []):
        if _check_show_function(choice, script):
            conversation.add(_read_choice(choice, script))
    return conversation
