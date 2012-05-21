

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
        self.parent.current_choice = self
        return self.response

    def matches(self, query_text):
        return query_text == self.query_text


def choice(query_text, response, *choices):
    return RespondChoice(query_text, response, choices)

def chat(*choices):
    return Conversation(choices)
