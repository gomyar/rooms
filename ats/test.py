import time
from rooms.pyclient import RoomsConnection

def test():
    conn = RoomsConnection("localhost", 8082)

    conn.create_game(owner_username="bob", game_id="735700000000000000000000")

    print "Getting info"
    info = conn.player_info("bob", "735700000000000000000000")
    print info
    if not info:
        print "Joining game"
        conn.join_game("bob", "735700000000000000000000", "area1", "room1",
            start_state="some value")
    else:
        print "Connecting to game"
        conn.connect_to_game("bob", "735700000000000000000000")

    # move in a square
    while True:
        conn.call("move_to", x=100, y=100)
        time.sleep(1)
        conn.call("move_to", x=300, y=100)
        time.sleep(1)
        conn.call("move_to", x=300, y=300)
        time.sleep(1)
        conn.call("move_to", x=100, y=300)
        time.sleep(1)


if __name__ == "__main__":
    test()
