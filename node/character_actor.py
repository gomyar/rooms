
from eventlet import sleep

from actor import Actor
from actor import get_now


class Action(object):
    def __init__(self, action_id, seconds=0.0, data={}):
        self.action_id = action_id
        self.seconds = seconds
        self.data = data
        self.start_time = get_now()
        self.end_time = self.start_time + seconds

    def external(self):
        return dict(action_id=self.action_id, seconds=self.seconds,
            data=self.data, start_time=self.start_time,
            end_time=self.end_time)


class CharacterActor(Actor):
    def __init__(self, actor_id, position=(0, 0)):
        super(CharacterActor, self).__init__(actor_id, position)
        self.stats = dict()
        self.action = Action("standing")
        self.model_type = ""

    def external(self):
        ext = Actor.external(self)
        ext['action'] = self.action.external()
        ext['stats'] = self.stats
        ext['model_type'] = self.model_type
        return ext

    def path_end_time(self):
        return self.path[-1][2]

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

    def perform_action(self, action_id, seconds=0.0, **data):
        self.action = Action(action_id, seconds, data)
        self.send_actor_update()
        sleep(seconds)

    def stop_walking(self):
        self.set_position(self.position())

    def move_to(self, x, y):
        x, y = float(x), float(y)
        path = self.room.get_path((self.x(), self.y()), (x, y))
        if not path or len(path) < 2:
            raise Exception("Wrong path: %s" % (path,))
        self.set_path(path)
        self.send_actor_update()
        end_time = self.path_end_time()
        sleep(end_time - get_now())

    def send_actor_update(self):
        self.send_to_players_in_room("actor_update", **self.external())

    def walk_towards(self, actor):
        self.move_to(actor.x(), actor.y())

    def say_to_room(self, message):
        players = self.room.all_players()
        for player in players:
            player.add_chat_message(message)

    def roll(self, stats, seconds):
        return True
