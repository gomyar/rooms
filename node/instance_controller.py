

def _call_node(host, port, method, data):
    response = urllib2.urlopen("http://%s:%s/control/%s" % (host, port, method),
        urllib.urlencode(data)).read()
    return simplejson.loads(response)


class NodeStub:
    def __init__(self, host, port):
        self.instances = 0
        self.players = 0
        self.host = host
        self.port = port

    def instance_count(self):
        return self.instances

    def create_instance(self, map_id):
        response = _call_node(self.host, self.port, "create_instance",
            dict(map_id=map_id))
        self.instances += 1
        return response['instance_uid']

    def player_joins(self, player_id, instance_uid):
        response = _call_node(self.host, self.port, "player_joins",
            dict(player_id=player_id, instance_uid=instance_uid))
        self.players += 1
        return response



class InstanceController(object):
    def __init__(self):
        self.nodes = dict()
        self.instances = dict()
        self.players = dict()

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


