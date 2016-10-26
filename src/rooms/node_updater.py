

class NodeUpdater(object):
    def __init__(self, node):
        self.node = node
        self.running = False

    def update_loop(self):
        self.running = True
        while self.running:
            self.send_onlinenode_update()
            Timer.sleep(1)

    def send_onlinenode_update(self):
        self.node.container.onlinenode_update(self.node.name, self.node.host,
                                              self.node.load)
