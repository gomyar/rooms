
from rooms.rpc import request


class AdminController(object):
    def __init__(self, container):
        self.container = container

    @request
    def list_nodes(self):
        return self.container.list_nodes()

    @request
    def list_rooms(self, active=True, node_name=None, game_id=None):
        return self.container.list_rooms(active=active, node_name=node_name,
                                         game_id=game_id)

    @request
    def list_games(self, owner_id=None, node_name=None):
        return self.container.list_games(owner_id, node_name)

    @request
    def list_players(self, node_name=None):
        return self.container.list_players(node_name)
