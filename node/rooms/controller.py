
from wsgi_rpc import WSGIRPCClient
from wsgi_rpc import WSGIRPCServer


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
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.nodes = dict()
        self.instances = dict()
        self.wsgi_server = None

    def init(self):
        self.wsgi_server = WSGIRPCServer(self.host, self.port,
            exposed_methods=dict(
                register_node=self.register_node,
                deregister_node=self.deregister_node,
                create_instance=self.create_instance,
                join_instance=self.join_instance,
                player_left=self.player_left,
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

    def create_instance(self, area_id):
        node = self._least_busy_node()
        instance_uid = node.client.create_instance(area_id=area_id)
        instance = dict(players=[],
            node=(node.host, node.port),
            area_id=area_id, uid=instance_uid)
        self.instances[instance_uid] = instance
        return instance

    def join_instance(self, user_id, instance_uid):
        instance = self.instances[instance_uid]
        if user_id not in instance['players']:
            instance['players'].append(user_id)
        node = self.nodes[instance['node']]
        node.client.player_joins(instance_uid=instance_uid, player_uid=user_id)
        return dict(success=True, node=(node.external_host, node.external_port))

    def player_left(self, user_id, instance_uid):
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
        self.master.register_node(self.host, self.port, self.node.host,
            self.node.port)

    def deregister_with_master(self):
        self.master.deregister_node(self.host, self.port)

    def init(self):
        self.master = WSGIRPCClient(self.master_host, self.master_port)
        self.wsgi_server = WSGIRPCServer(self.host, int(self.port),
            dict(create_instance=self.create_instance,
                player_joins=self.player_joins))

    def start(self):
        self.wsgi_server.start()

    def create_instance(self, area_id):
        return self.node.create_instance(area_id)

    def player_joins(self, instance_uid, player_uid):
        return self.node.player_joins(instance_uid, player_uid)
