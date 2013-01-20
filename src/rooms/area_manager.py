
import gevent

import logging
log = logging.getLogger("rooms.areamanager")


class AreaManager(object):
    def __init__(self, area, container):
        self.area = area
        self.container = container
        self.running = True
        self.gthread = None

    def run_save(self):
        for room in self.area.rooms._rooms.values():
            self.save_room(room)
            if not room.all_players():
                self.icicle_room(room)

    def save_room(self, room):
        log.debug("Saving room: %s", room)
        self.container.save_room(room)

        players = room.all_players()
        if players:
            for player in players:
                self.container.save_player(player.player)

    def icicle_room(self, room):
        self.area.rooms._rooms.pop(room.room_id)

    def shutdown(self):
        self.running = False
        self.gthread.join()
        for room in self.area.rooms._rooms.values():
            self.save_room(room)
            self.icicle_room(room)

    def run_manager(self):
        while self.running:
            self.run_save()

    def start(self):
        self.gthread = gevent.spawn(self.run_manager)
