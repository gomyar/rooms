
from wsgi_rpc import WSGIRPCClient
from wsgi_rpc import WSGIRPCServer

from rooms.script_wrapper import Script


class RegisteredNode(object):
    def __init__(self, host, port, external_host, external_port):
        self.client = WSGIRPCClient(host, port)
        self.host = host
        self.port = port
        self.external_host = external_host
        self.external_port = external_port

    def __eq__(self, rhs):
        return type(rhs) is RegisteredNode and self.host == rhs.host and \
            self.port == rhs.port and self.external_host == rhs.external_host \
            and self.external_port == self.external_port


class MasterController(object):
    def __init__(self, config, host, port, container):
        self.host = host
        self.port = port
        self.nodes = dict()
        self.instances = dict()
        self.wsgi_server = None
        self.config = config
        self.container = container

    def init(self):
        self.create_script = Script(self.config.get('scripts', 'create_script'))
        self.wsgi_server = WSGIRPCServer(self.host, self.port,
            exposed_methods=dict(
                register_node=self.register_node,
                deregister_node=self.deregister_node,

                create_game=self.create_game,
                join_game=self.join_game,
                leave_game=self.leave_game,
                player_info=self.player_info,

                list_instances=self.list_instances,
                instance_info=self.instance_info,
            )
        )

    def start(self):
        self.wsgi_server.start()

    def register_node(self, host, port, external_host, external_port):
        self.nodes[host, port] = RegisteredNode(host, port, external_host,
            external_port)

    def deregister_node(self, host, port):
        self.nodes.pop((host, port))
        for uid, instance in self.instances.items():
            if instance['node'] == (host, port):
                self.instances.pop(uid)

    def _get_or_create_player(self, player_id):
        return self.container.get_or_create_player(player_id)

    def player_info(self, player_id):
        player = self._get_or_create_player(player_id)
        return dict(
            username=player.username,
            game_id=player.game_id,
            instance_id=player.instance_id,
            actor_id=player.instance_id,
        )

    def create_game(self, player_id):
        # run create script
        player = self._get_or_create_player(player_id)
        game = self.create_script.call_method("create_game", self)
        area_id = game.start_area_id()
        # tell node to manage area
        node = self._least_busy_node()
        instance_uid = node.client.manage_area(area_id=area_id)
        instance = dict(players=[],
            node=(node.host, node.port),
            area_id=area_id, uid=instance_uid)
        self.instances[instance_uid] = instance
        player.game_id = str(game._id)
        player.instance_id = instance_uid
        self.container.save_player(player)
        return instance

    def join_game(self, user_id, instance_uid):
        instance = self.instances[instance_uid]
        if user_id not in instance['players']:
            instance['players'].append(user_id)
        node = self.nodes[instance['node']]
        node.client.player_joins(instance_uid=instance_uid, player_uid=user_id)
        return dict(success=True, node=(node.external_host, node.external_port))

    def leave_game(self, user_id, instance_uid):
        instance =  self.instances[instance_uid]
        instance['players'].remove(user_id)
        log.debug("Player %s left instance %s", user_id, instance_uid)
        return ""

    def list_instances(self):
        return self.instances

    def instance_info(self, instance_uid):
        return self.instances[instance_uid]

    def _least_busy_node(self):
        return self.nodes.values()[0]


class ClientController(object):
    def __init__(self, node, host, port, master_host, master_port):
        self.node = node
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
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
                player_joins=self.player_joins))

    def start(self):
        self.wsgi_server.start()

    def manage_area(self, area_id):
        return self.node.manage_area(area_id)

    def player_joins(self, instance_uid, player_uid):
        return self.node.player_joins(instance_uid, player_uid)
