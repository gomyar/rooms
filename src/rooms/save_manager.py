
import gevent

import logging
log = logging.getLogger("rooms.savemanager")


class SaveManager(object):
    def __init__(self, node, container):
        self.node = node
        self.container = container
        self.running = True
        self.gthread = None

    def run_save(self):
        for area in self.node.areas.values():
            for room in area.rooms.values():
                self.save_room(room)
                if not room.player_actors():
                    area.rooms.pop(room.room_id)

    def save_room(self, room):
        log.debug("Saving room: %s", room)
        self.container.save_room(room)

        players = room.player_actors()
        if players:
            for player in players:
                self.container.save_player(player.player)

    def shutdown(self):
        self.running = False
        self.gthread.join()
        for area in self.node.areas.values():
            for room in area.rooms.values():
                self.save_room(room)
                area.rooms.pop(room.room_id)

    def run_manager(self):
        while self.running:
            self.run_save()

    def start(self):
        self.gthread = gevent.spawn(self.run_manager)
