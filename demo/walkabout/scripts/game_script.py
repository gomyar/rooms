

def start_room(**kwargs):
    return "map1.room1"


def room_created(room):
    for tag in room.find_tags("actor.spawn"):
        room.create_actor(tag.data['actor_type'], tag.data['actor_script'])
