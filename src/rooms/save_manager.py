
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
        while self.queue:
            actor = self.queue.pop(0)
            log.debug("Updating actor: %s", actor)
            self.container.update_actor(actor)
            gevent.sleep(0.1)
            self.check_invalid_rooms()
        gevent.sleep(0.1)

    def check_invalid_rooms(self):
        for area in self.node.areas.values():
            for room in area.rooms.values():
                if not room.player_actors():
                    self.save_room(room)
                    area.rooms.pop(room.room_id)
                gevent.sleep(0.1)

    def queue_actor(self, actor): # , room) ?
        if actor not in self.queue:
            self.queue.append(actor)

    def queue_actor_remove(self, actor):
        pass

    def save_room(self, room):
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

    def _killall_actors(self):
        for area in self.node.areas.values():
            for room in area.rooms.values():
                for actor in room.actors.values():
                    actor.kill_gthread()

    def shutdown(self):
        log.debug("Shutting down save manager")
        self.running = False
        self.gthread.join()
        self._killall_actors()
        for area in self.node.areas.values():
            for room in area.rooms.values():
                self.save_room(room)
                area.rooms.pop(room.room_id)
            self.container.save_area(area)
        log.debug("Save manager shut down")
