
from scriptutils import load_script
from script import *

from scripts.WanderingNpcScript import WanderingNpcScript
from scripts.ButlerScript import ButlerScript
from scripts.GladysScript import GladysScript
from scripts.JezabelScript import JezabelScript
from scripts.AuntScript import AuntScript
from scripts.ProfessorScript import ProfessorScript
from scripts.MajorScript import MajorScript
from scripts.DilettanteScript import DilettanteScript

from npc_actor import NpcActor


class MansionGameScript(Script):
    def kickoff(self, area):
        area.add_npc(NpcActor("butler", load_script("ButlerScript")), 'foyer')
        area.add_npc(NpcActor("dilettante", load_script("DilettanteScript")),
            'study')
        area.add_npc(NpcActor("gladys", load_script("GladysScript")),
            'diningroom')
        area.add_npc(NpcActor("jezabel", load_script("JezabelScript")),
            'diningroom')
        area.add_npc(NpcActor("major", load_script("MajorScript")),
            'trophyroom')
        area.add_npc(NpcActor("professor", load_script("ProfessorScript")),
            'library')
        area.add_npc(NpcActor("aunt", load_script("AuntScript")),
            'lounge')

    def event_player_joins_instance(self, player):
        pass
