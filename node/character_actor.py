
from actor import Actor
from actor import get_now


class CharacterActor(Actor):
    def get_stat(self, stat):
        return self.stats.get(stat, 0)

    def send_to_characters_in_room(self, event, **kwargs):
        players = self.room.all_characters()
        player_ids = [player.actor_id for player in players]
        self.instance.send_to_players(player_ids, event, **kwargs)

    def send_to_players_in_room(self, event, **kwargs):
        players = self.room.all_players()
        player_ids = [player.actor_id for player in players]
        self.instance.send_to_players(player_ids, event, **kwargs)

    def stop_walking(self):
        self.set_position(self.position())

    def say_to_room(self, message):
        players = self.room.all_players()
        for player in players:
            player.add_chat_message(message)

    def roll(self, stats, seconds):
        return True
