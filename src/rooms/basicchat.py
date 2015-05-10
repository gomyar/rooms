
class Chat(object):
    def __init__(self, state, chatdata):
        self.pointer_path = state.split('.')
        self.chat = chatdata

    def start_conversation(self, player, actor):
        index, snippet = self._find_top_snippet(player, actor)
        player._set_state_val(self.pointer_path, [index])
        return self._filter_choices(snippet, player, actor)

    def _find_top_snippet(self, player, actor):
        for index, snippet in enumerate(self.chat):
            if self._is_current_snippet(snippet, player, actor):
                return index, snippet
        return 0, {}

    def _filter_choices(self, snippet, player, actor):
        return {"msg": snippet['msg'],
            "choices": [(index, choice) for (index, choice) in \
                enumerate(snippet['choices']) if \
                self._is_current_snippet(choice, player, actor)]
        }

    def respond(self, player, actor, choice_index):
        snippet = self._find_snippet(player)
        chosen = snippet['choices'][choice_index]
        self._perform_snippet_actions(player, actor, chosen)
        if chosen and chosen.get('choices'):
            chat_pointer = player._get_state_val(self.pointer_path)
            chat_pointer.append(choice_index)
            player._set_state_val(self.pointer_path, chat_pointer)
            return self._filter_choices(chosen['choices'][choice_index],
                player, actor)
        else:
            start_snippet = self.start_conversation(player, actor)
            return {"msg": chosen['msg'],
                "choices": start_snippet.get("choices", {})}

    def _perform_snippet_actions(self, player, actor, chosen):
        # perform state / call / set
        for key, value in chosen.get('set', {}).items():
            player._set_state_val(key.split('.'), value)

    def _find_snippet(self, player, current=None):
        chat_pointer = player._get_state_val(self.pointer_path)
        snippet = self.chat[chat_pointer[0]]
        current = snippet
        for index in chat_pointer[1:]:
            current = snippet['choices'][index]
        return current

    def _is_current_snippet(self, snippet, player, actor):
        if 'test' in snippet:
            criteria = snippet['test']
            return all(self._is_true(key, value, player) for \
                key, value in criteria.items())
        else:
            return True

    def _is_true(self, key, value, player):
        return player._get_state_val(key.split('.')) == value
