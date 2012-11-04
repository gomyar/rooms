
from rooms.script import *

def init(area):
    create_npc(area, "butler", "ButlerScript", 'foyer')
    create_npc(area, "dilettante", "DilettanteScript", 'study')
    create_npc(area, "gladys", "GladysScript", 'diningroom')
    create_npc(area, "jezabel", "JezabelScript", 'diningroom')
    create_npc(area, "major", "MajorScript", 'trophyroom')
    create_npc(area, "professor", "ProfessorScript", 'library')
    create_npc(area, "aunt", "AuntScript", 'lounge')
