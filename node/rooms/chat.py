

class Conversation:
    def __init__(self, choices=[]):
        self.choices = choices
        self.current_choice = self
        for choice in choices:
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
    def __init__(self, query_text, response, choices=[]):
        self.query_text = query_text
        self.response = response
        self.choices = choices
        self.parent = None

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
