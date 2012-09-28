from script import *

def kickoff(npc):
    if npc.room.room_id == "diningroom":
        npc.say("Hmph")
        move_to_object(npc, "diningroom_chair_b1")
        npc.sleep(5)
        npc.say("It's all ruined, everything's ruined...")
        move_to_object(npc, "diningroom_chair_l4")
        npc.state.moving_to = "lounge"
    
        npc.move_to_room("hall")
    if npc.room.room_id == "hall":
        npc.say("Deary me...")
        if npc.state.moving_to == "lounge":
            npc.move_to_room("lounge")
        else:
            npc.move_to_room("diningroom")
    if npc.room.room_id == "lounge":
        npc.move_to(100, 1200)
        npc.say("It's awful, just awful...")
        npc.sleep(4)
        npc.state.moving_to = "diningroom"
        npc.move_to_room("hall")
