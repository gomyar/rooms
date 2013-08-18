
def create_game(game):
    area1 = game.create_area("area1")

    room1 = area1.create_room("room1", (0, 0), 500, 500, "Test Room")
