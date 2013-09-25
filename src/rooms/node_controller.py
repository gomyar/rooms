
from rooms.wsgi_rpc import WSGIRPCClient
from rooms.wsgi_rpc import WSGIRPCServer

import logging

log = logging.getLogger("rooms.nodecontroller")


class NodeController(object):
    def __init__(self, node, host, port, master_host, master_port):
        self.node = node
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.master = None
        self.wsgi_server = None

    def register_with_master(self):
        self.master.register_node(host=self.host, port=self.port,
            external_host=self.node.host, external_port=self.node.port)

    def deregister_from_master(self):
        self.master.deregister_node(host=self.host, port=self.port)

    def init(self):
        self.master = WSGIRPCClient(self.master_host, self.master_port)
        self.wsgi_server = WSGIRPCServer(self.host, int(self.port),
            dict(manage_area=self.manage_area,
                player_joins=self.player_joins,
                admin_joins=self.admin_joins,
                admin_show_area=self.admin_show_area,
                load_from_limbo=self.load_from_limbo,
                send_message=self.send_message,
                ))

    def start(self):
        self.wsgi_server.start()

    def send_message(self, from_actor_id, actor_id, room_id, area_id, message):
        self.node.send_message(from_actor_id, actor_id, room_id, area_id,
            message)

    def load_from_limbo(self, area_id):
        self.node.load_from_limbo(area_id=area_id)

    def manage_area(self, game_id, area_id):
        log.debug("Managing area: %s", area_id)
        self.node.manage_area(game_id, area_id)

    def player_joins(self, username, game_id):
        player = self.node.container.load_player(username=username,
            game_id=game_id)
        return self.node.player_joins(game_id, player.area_id, player)

    def admin_joins(self, username, game_id, area_id, room_id):
        return self.node.admin_joins(username, game_id, area_id, room_id)

    def _roominfo(self, room):
        info = room.external(False)
        info['players'] = len([p for p in self.node.players.values() if \
            p['connected'] and p['player'].room.room_id == room.room_id])
        return info

    def admin_show_area(self, area_id):
        area = self.node.areas[area_id]
        rooms = dict([(room.room_id, self._roominfo(room)) for room in \
            area.rooms.values()])
        return dict(active_rooms=rooms, area_id=area_id,
            node_addr=self.node.host, node_port=self.node.port)
