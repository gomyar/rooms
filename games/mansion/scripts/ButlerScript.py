
import random

from script import *

evidence = [
    dict(category="means", actor="butler", description="The butler is a "
        "former army sergeant with hand to hand combat training"),
    dict(category="motive", actor="butler", description="The butler was "
        "about to be fired"),
    dict(category="opportunity", actor="butler", description="The butler was "
        "seen entering the cloakroom at the time of the murder"),
]


class ButlerScript(Script):
    def kickoff(self):
        self.set_state("greeting_guests")

    def state_greeting_guests(self):
        while True:
            self.walk_to(930, 1740)
            self.sleep(5)
            self.walk_to(1180, 1740)
            self.sleep(5)
            self.walk_to(1180, 1590)
            self.sleep(5)
            self.walk_to(930, 1590)
            self.sleep(5)

    def give_evidence_means(self, player):
        player.notes['butler'] = dict(category="means",
            actor="butler", description="The butler is a "
            "former army sergeant with hand to hand combat training")
        player.add_chat_message("You learned something")

    def chat(self, player):
        return chat(
            c("Hullo Jeeves", "Good evening, Sir",
                c("Have all the guests arrived yet?", "Not quite, Sir",
                    c("When is dinner starting?", "Around 9, Sir"),
                    c("Where is the owner?",
                        "Lady Pinkerton in in the dining room, Sir"),
                ),
                c("Yes, thank you Jeeves, any chance of a drink?",
                    "The Lounge is straight ahead on the left, Sir"),
                c("Where were you at the time of the murder?",
                    call(self.give_evidence_means, player)),
            )
        )
