
from rooms.timer import Timer


def kickoff(actor):
    actors = actor.room.actors['id2']
    target = actors[0]
    actor.state.start_time = Timer.now()
    actor.track_vector(target, 10)
    actor.state.end_time = Timer.now()
