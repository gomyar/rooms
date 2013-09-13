
from rooms.item_registry import Item


def create_game(game):
    area1 = game.create_area("area1")

    room1 = area1.create_room("room1", (0, 0), 500, 500, "Test Room")

    game.item_registry.add_item(Item("silver", "commodity", 100))

    room1.create_actor("misteractor", "misteractor_script")
