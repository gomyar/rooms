
import simplejson


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

class Call:
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        return self._func(*self._args, **self._kwargs)

def choice(query_text, response, *choices):
    return RespondChoice(query_text, response, choices)

def chat(*choices):
    return Conversation(list(choices))

def call(func, *args, **kwargs):
    return Call(func, *args, **kwargs)

def _read_choice(choice_json):
    choice = RespondChoice(choice_json['request'], choice_json['response'])
    for inner in choice_json.get('choices', []):
        choice.choices.append(_read_choice(inner))
    return choice

def load_chat(chat_id):
    chat_json = simplejson.loads(open(chat_id + ".json").read())
    conversation = Conversation()
    for choice in chat_json.get('choices', []):
        conversation.add(_read_choice(choice))
    return conversation
