
import logging
log = logging.getLogger("rooms.container")


class Container(object):
    def save_game(self, game):
        log.debug("Saving game %s", game)
        game.game_id = "1"
