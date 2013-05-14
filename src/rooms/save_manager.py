
import gevent

import logging
log = logging.getLogger("rooms.savemanager")


class SaveManager(object):
    def __init__(self, node, container):
        self.node = node
        self.container = container
        self.running = True
        self.gthread = None
        self.queue = []

    def run_save(self):
        while self.queue and self.running:
            actor = self.queue.pop(0)
            if actor.room:
                self.container.update_actor(actor)
            gevent.sleep(0.1)
            self.check_invalid_rooms()
        gevent.sleep(0.1)

    def update_player_location(self, player, area_id, room_id):
        self.container.update_player_location(player, area_id, room_id)
        if player in self.queue:
            self.queue.remove(player)

    def check_invalid_rooms(self):
        for area in self.node.areas.values():
            for room in area.rooms.values():
                if not room.player_actors():
                    log.debug("Icicling room %s", room)
                    self._kill_room_actors(room)
                    self.save_room(room)
                    area.rooms.pop(room.room_id)
                    return

    def queue_actor(self, actor): # , room) ?
        if actor not in self.queue:
            self.queue.append(actor)

    def queue_actor_remove(self, actor):
        room = actor.room
        if actor in self.queue:
            self.queue.remove(actor)
        self.container.remove_actor(room, actor)

    def save_room(self, room):
        self.container.save_room(room)

        players = room.player_actors()
        if players:
            for player in players:
                self.container.save_player(player.player)

    def run_manager(self):
        while self.running:
            self.run_save()

    def start(self):
        self.gthread = gevent.spawn(self.run_manager)

    def _kill_room_actors(self, room):
        for actor in room.actors.values():
            actor.kill_gthread()

    def _killall_actors(self):
        for area in self.node.areas.values():
            for room in area.rooms.values():
                self._kill_room_actors(room)

    def shutdown(self):
        log.debug("Shutting down save manager")
        self.running = False
        if self.gthread:
            self.gthread.join()
        self._killall_actors()
        for area in self.node.areas.values():
            for room in area.rooms.values():
                self.save_room(room)
                area.rooms.pop(room.room_id)
            self.container.save_area(area)
        log.debug("Save manager shut down")
