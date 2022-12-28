
import gevent
from rooms.timer import Timer


class NodeUpdater(object):
    def __init__(self, node):
        self.node = node
        self.running = False
        self._gthread = None

    def start(self):
        self.running = True
        self._gthread = gevent.spawn(self.update_loop)

    def stop(self):
        self.running = False
        if self._gthread:
            self._gthread.join()

    def update_loop(self):
        try:
            while self.running:
                self.send_onlinenode_update()
                Timer.sleep(1)
        except Exception as e:
            log.exception("Exception updating node")

    def send_onlinenode_update(self):
        self.node.container.onlinenode_update(self.node.name, self.node.host,
                                              self.node.load)
