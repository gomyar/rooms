

class VisibilityFilter(object):
    def __init__(self):
        self.listeners = set()

    def add_listener(self, listener):
        self.listeners.add(listener)

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def actor_vector_changed(self, actor):
        ''' Called when actor vector changes '''
        for listener in self.listeners:
            listener.actor_update(actor)

    def actor_state_changed(self, actor):
        ''' Called when actor state changes '''
        for listener in self.listeners:
            listener.actor_update(actor)

    def actor_removed(self, actor):
        ''' Called when actor destroyed or leaves room '''
        for listener in self.listeners:
            listener.remove_actor(actor)

    def actor_added(self, actor):
        ''' Called when actor added to room '''
        for listener in self.listeners:
            listener.actor_update(actor)

    def actor_becomes_visible(self, actor):
        ''' Called when actor becomes visible '''
        for listener in self.listeners:
            listener.actor_update(actor)

    def actor_becomes_invisible(self, actor):
        ''' Called when actor becomes invisible '''
        for listener in self.listeners:
            listener.remove_actor(actor)
