
import logging
log = logging.getLogger("rooms.container")


class Container(object):
    def save_game(self, game):
        log.debug("Saving game %s", game)
        game.game_id = "1"

    def save_player(self, player):
        log.debug("Saving player %s", player)

    def load_room(self, game_id, room_id):
        return None

    def save_room(self, room):
        pass

    def room_exists(self, game_id, room_id):
        return False
