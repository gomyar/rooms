
class AdminController(object):
    def __init__(self, master):
        self.master = master

    def list_areas(self):
        # get room info from node?
        return self.master.areas

    def show_nodes(self):
        nodes = dict([("%s:%s" % (host, port), node.external()) for \
            ((host, port), node) in self.master.nodes.items()])
        return nodes

    def show_area(self, area_id):
        host, port = self.master.areas[area_id]['node']
        rooms = self.master.nodes[host, port].client.admin_show_area(
            area_id=area_id)
        return rooms
