import time
from rooms.pyclient import RoomsConnection

conn = RoomsConnection()

info = conn.player_info("bob", "735700000000000000000000")
print info
if not info:
    conn.join_game("bob", "735700000000000000000000", "mu_sector", "new_sol",
        alliance_id="federal", ship_type="ship_bulldog", money=100)
else:
    conn.connect_to_game("bob", "735700000000000000000000")

time.sleep(5)
