
import unittest

from chat import Conversation
from chat import RespondChoice
from chat import chat
from chat import choice


class ChatTest(unittest.TestCase):
    def setUp(self):
        self.choice1 = RespondChoice("hello", "hello yourself")
        self.choice_inner = RespondChoice("moi", "moi yourself")
        self.choice2 = RespondChoice("there", "there yourself", [
            self.choice_inner,
        ])
        self.chat = Conversation([
            self.choice1,
            self.choice2,
        ])

    def testInteraction(self):
        self.assertEquals(["hello", "there"], self.chat.choice_list())
        self.assertEquals(self.choice1.response, self.chat.said("hello"))
        self.assertEquals([], self.chat.choice_list())
        self.assertEquals(None, self.chat.said("nothing"))

        self.chat.reset()
        self.assertEquals(["hello", "there"], self.chat.choice_list())
        self.assertEquals(self.choice2.response, self.chat.said("there"))
        self.assertEquals(['moi'], self.chat.choice_list())
        self.assertEquals(self.choice_inner.response, self.chat.said("moi"))
        self.assertEquals([], self.chat.choice_list())

    def testTaggedChoices(self):
        self.chat = chat(
            choice("question1", "answer1",
                choice("question2", "answer2",
                        choice("done", "ok then")
                ),
            ),
        )

        self.assertEquals(['question1'], self.chat.choice_list())
        self.assertEquals("answer1", self.chat.said("question1"))
        self.assertEquals(['question2'], self.chat.choice_list())
        self.assertEquals("answer2", self.chat.said("question2"))
        self.assertEquals(['done'], self.chat.choice_list())
        self.assertEquals("ok then", self.chat.said("done"))
        self.assertEquals([], self.chat.choice_list())

'''
        @hasnt_talked_to_butler_before
        "hello jeeves", "hello, sir"
            "where is laddy chatterly?", "in the boardroom, sir"
            "could you give me a scotch?", give_scotch
        @has_talked_to_professor
        "tell me about the professor", "I'm sure I don't know sir"
            "but you must know something", "he goes to the basement a lot"
            "could you fetch him for me", fetch_professor
        @has_learned_about_diletent
        "about mister diletent", "oh, him. yes?"
            "did you know he was chatterly's lover", "so?"
                "so I also found out he has the jade monkey", open_basement
                "I suppose its none of my business", "youre right there sir"

        {
        'default':
            c("hello jeeves", "hello, sir",
                c("where is laddy chatterly?", "in the boardroom, sir"),
                c("could you give me a scotch?", give_scotch),
            ),
        'has_talked_to_professor':
            c("tell me about the professor", "I'm sure I don't know sir",
                c("but you must know something",
                    "he goes to the basement a lot"),
                c("could you fetch him for me", fetch_professor),
            ),
        'has_learned_about_diletent':
            c("about mister diletent", "oh, him. yes?",
                c("did you know he was chatterly's lover", "so?",
                    c("so I also found out about the jade monkey",
                        open_basement),
                    c("I suppose its none of my business",
                        "youre right there sir"),
                ),
            ),
        }
'''

#    def testListOfChoices(self):
#        self.chat = chat(
#            choice("first", "question1", "answer1", "second"),
#        )
