
from actor import Actor


class CharacterActor(Actor):
    def __init__(self, actor_id, position=(0, 0)):
        super(CharacterActor, self).__init__(actor_id, position)
        self.stats = dict()
        self.roll_system = None

    def send_to_characters_in_room(self, event, **kwargs):
        players = self.room.all_characters()
        player_ids = [player.actor_id for player in players]
        self.instance.send_to_players(player_ids, event, **kwargs)

    def send_to_players_in_room(self, event, **kwargs):
        players = self.room.all_players()
        player_ids = [player.actor_id for player in players]
        self.instance.send_to_players(player_ids, event, **kwargs)

    def say_to_room(self, message):
        players = self.room.all_players()
        for player in players:
            player.add_chat_message(message)

    def roll(self, stat_list):
        return self.roll_system.roll(self, stat_list)
