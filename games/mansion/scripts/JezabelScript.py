
import random

from script import *


class JezabelScript(Script):
    def kickoff(self):
        self.set_state("pottering_around_dining_room")

    def state_pottering_around_dining_room(self):
        while True:
            self.walk_to(830, 620)
            self.sleep(2)
            self.walk_to(860, 460)
            self.sleep(3)
            self.walk_to(850, 690)
            self.sleep(2)
            self.walk_to(1170, 690)
            self.sleep(3)
            self.walk_to(1030, 720)
            self.sleep(5)

    def storm_off(self, player):
        self.say("That's rude. Leave me alone")
        self.set_state("pottering_around_dining_room")
        player.data.jezabel_is_defensive = True

    def chat(self, player):
        conv = chat(
            c("Excuse me madame", "What? Yes, what do you want?",
                c("When will dinner be ready?",
                    "How should I know?"),
                c("Where were you at the time of the murder?",
                    call(self.storm_off, player)),
                c("Well, is there a snack ready?",
                    "How would I know? Ask the cook."),
            )
        )
        if player.data.jezabel_ask_about_paris:
            conv.add(c("I hear you were in Paris this season...",
                "Oh, yes, wonderful city. All those lights.",
                    c("Um hm.",
                        "And the food, I though I should just burst",
                        c("I see",
                            "And the music, it was glorious, so many "
                            "operettos...",
                            c("Uh huh. So about this murder...",
                                "And the walks we used to take, along the "
                                "change elyse",
                                c("I may have to talk to another guest...",
                                    "Yes we spent so much time in the vinyards"
                                    " as well, they have the very best wine in"
                                    " France you know",
                                    c("I really must...",
                                        "Yes of course"
                                    )
                                )
                            )
                        )
                    )
                )
            )
        return conv
