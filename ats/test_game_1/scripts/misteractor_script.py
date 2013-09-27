
def kickoff(npc):
    npc.move_to(0, 0)
    npc.sleep(1)
    npc.move_to(10, 10)

    while True:
        npc.move_to(20, 20)
        npc.move_to(20, 30)
        npc.move_to(30, 30)
        npc.move_to(30, 20)
