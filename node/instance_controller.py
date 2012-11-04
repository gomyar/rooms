import urllib2
import urllib
import simplejson

from wsgi_rpc import WSGIRPCClient

from utils import checked

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import logging
import logging.config
logging.config.fileConfig("logging.conf")
log = logging.getLogger("rooms.controller")


class NodeStub(object):
    def __init__(self, host, port):
        self.instances = 0
        self.players = 0
        self.host = host
        self.port = port
        self.wsgi_client = WSGIRPCClient(host, port)

    def instance_count(self):
        return self.instances

    def create_instance(self, map_id):
        response = self.wsgi_client.create_instance(map_id=map_id)
        self.instances += 1
        return response['instance_uid']

    def player_joins(self, player_id, instance_uid):
        response = self.wsgi_client.player_joins(player_id=player_id,
            instance_uid=instance_uid)
        self.players += 1
        return response


class InstanceController(object):
    def __init__(self, node):
        self.node = node
        self.nodes = dict()
        self.instances = dict()
        self.players = dict()

    def init(self, options):
        self.host, self.port = options.controller_api.split(':')
        if options.controller_address:
            log.info("Connecting to Controller at %s",
                options.controller_address)
            self.register_with_controller(options.controller_address)
            # share client xmlrpc
            self._start_wsgi_server(self.handle_client)
        else:
            log.info("Assuming Controller role")
            stub = NodeStub('', 0)
            stub.create_instance = self.create_instance
            stub.player_joins = self.player_joins
            self.nodes[('', 0)] = stub
            # share master xmlrpc
            self._start_wsgi_server(self.handle_controller)

    def _start_wsgi_server(self, handle):
        server = pywsgi.WSGIServer((self.host, int(self.port)), handle,
            handler_class=WebSocketHandler)
        server.start()

    @checked
    def handle_controller(self, environ, response):
        if not self.node.controller:
            raise Exception("This is not a Controller node")

        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        controller_call = environ['PATH_INFO'].replace('/controller/', '')
        controller_method = getattr(self.node.controller, controller_call)
        returned = controller_method(**params)
        if returned :
            returned = simplejson.dumps(returned)
        else:
            returned = "[]"
        response('200 OK', [
            ('content-type', 'text/javascript'),
            ('content-length', len(returned)),
        ])
        return returned

    def player_joins(self, instance_uid, player_id):
        self.node.player_joins(instance_uid, player_id)
        log.info("Player %s joined instance %s", player_id, instance_uid)
        return '{"success":true}'

    def create_instance(self, map_id):
        map_id = params['map_id']
        uid = self.node.create_instance(map_id)
        log.info("Instance created %s : %s", map_id, uid)
        return '{"instance_uid": "%s"}' % (uid,)


    @checked
    def handle_client(self, environ, response):
        path = environ['PATH_INFO'].replace("/control/", "")
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))

        returned = ""

        if path == "player_joins":
            returned = self.player_joins(instance_uid, player_id)

        if path == "create_instance":
            returned = self.create_instance(map_id)

        response('200 OK', [
            ('content-type', 'text/javascript'),
            ('content-length', len(returned)),
        ])
        return returned

    def register_with_controller(self, controller_address):
        self.controller = WSGIRPCClient(controller_address.split(':'))
        self.controller.register_node(self.host, self.port)

    def shutdown(self):
        if self.controller:
            self.controller.deregister_node(self.host, self.port)

    def register_node(self, host, port):
        self.nodes[(host, port)] = NodeStub(host, port)
        return True

    def deregister_node(self, host, port):
        print "Deregistering Node at %s:%s" % (host, port)
        stub = self.nodes.pop((host, port))
        for uid, instance in self.instances.items():
            if instance['node'] == (host, port):
                self.instances.pop(uid)
        return "Ok"

    def _least_busy_node(self):
        return min(self.nodes.values(), key=NodeStub.instance_count)

    def create_instance(self, user_id, map_id):
        node = self._least_busy_node()
        instance_uid = node.create_instance(map_id)
        instance = dict(players=[],
            node=(node.host, node.port),
            map_id=map_id, uid=instance_uid)
        self.instances[instance_uid] = instance
        return instance

    def join_instance(self, user_id, instance_uid):
        instance = self.instances[instance_uid]
        if user_id not in instance['players']:
            instance['players'].append(user_id)
        node = self.nodes[instance['node']]
        node.players += 1
        node.player_joins(instance_uid, user_id)
        self.players[user_id] = instance_uid
        return dict(success=True, node=(node.host, node.port))

    def player_left(self, user_id, instance_uid):
        instance =  self.instances[instance_uid]
        instance['players'].remove(user_id)
        node = self.nodes[instance['node']]
        node.players -= 1
        log.debug("Player %s left instance %s", user_id, instance_uid)
        return ""

    def list_instances(self):
        return self.instances

    def instance_info(self, instance_uid):
        return self.instances[instance_uid]

    def own_instance(self, player_id):
        for instance in self.instances.values():
            if player_id in instance['players']:
                return instance['uid']
        return ""


