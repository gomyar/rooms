
import uuid


class IDFactory(object):
    _instance = None

    @staticmethod
    def create_id():
        return IDFactory._instance._create_id()

    def _create_id(self):
        return str(uuid.uuid1())

IDFactory._instance = IDFactory()


def sort_actor_data(alist):
    def _reverse_iterpath(node):
        while node is not None:
            yield node
            node = node['_parent']

    def path(node):
        return tuple(_reverse_iterpath(node))[::-1]

    actors = dict([(a['actor_id'], a) for a in alist])
    for a in actors.values():
        a['_parent'] = actors[a['docked_with']] if a.get('docked_with') \
            in actors else None
    return sorted(actors.values(), key=path)
