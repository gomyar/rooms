import time
import gevent
from rooms.pyclient import RoomsConnection


def wait_for_sync(conn, timeout=1):
    now = time.time()
    while not conn.player_actor and time.time() < now + timeout:
        gevent.sleep(0.1)
    if not conn.player_actor:
        raise AssertionError("No sync occured after %s seconds" % (timeout,))


def wait_for_state(actor, state, value, timeout=1):
    now = time.time()
    while actor.state.get(state) != value and time.time() < now + timeout:
        gevent.sleep(0.1)
    if actor.state.get(state) != value:
        raise AssertionError("Actor %s state does not match: %s != %s" % (
            actor, actor.state.get(state), value))


def wait_for_position(actor, position, timeout=1):
    now = time.time()
    while actor.position() != position and time.time() < now + timeout:
        gevent.sleep(0.1)
    if actor.position() != position:
        raise AssertionError("Actor %s position does not match: %s != %s" % (
            actor, actor.position(), position))


def test():
    runner = RoomsTestRunner()
    runner.start_nodes(2)

    conn = RoomsConnection("localhost", 8082)

    conn.create_game(owner_username="bob", game_id="735700000000000000000000")

    info = conn.player_info("bob", "735700000000000000000000")
    if not info:
        print "Joining game"
        conn.join_game("bob", "735700000000000000000000", "area1", "room1",
            start_state="some value")
    else:
        print "Connecting to game"
        conn.connect_to_game("bob", "735700000000000000000000")

    wait_for_sync(conn)

    conn.call("set_position", x=100, y=100)
    wait_for_position(conn.player_actor, (100, 100))

    conn.call("move_to", x=300, y=100)
    wait_for_position(conn.player_actor, (300, 100), 2.5)


if __name__ == "__main__":
    test()
