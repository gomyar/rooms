
from actor import Actor


class CharacterActor(Actor):
    def __init__(self, actor_id, position=(0, 0)):
        super(CharacterActor, self).__init__(actor_id, position)

    def send_to_characters_in_room(self, event, **kwargs):
        players = [player for player in self.room.all_characters()]
        player_ids = [player.actor_id for player in players]
        self.instance.send_to_players(player_ids, event, **kwargs)

    def send_to_players_in_room(self, event, **kwargs):
        players = [player for player in self.room.all_players()]
        player_ids = [player.actor_id for player in players]
        self.instance.send_to_players(player_ids, event, **kwargs)
