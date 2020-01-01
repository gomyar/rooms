
import json
import os
import unittest
from flask import Flask
from rooms.flask.master import bp_master
from rooms.flask.node import bp_node
from rooms.flask.login import init_login
from rooms.flask.login import bp_login
from rooms.flask import app
from rooms.testutils import MockDbase


def start_room():
    return "map1.room1"


class FlaskAppTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        app.container.dbase = self.dbase
        self.app = Flask(__name__)
        self.app.secret_key = "1234test"
        self.app.register_blueprint(bp_master)
        self.app.register_blueprint(bp_node, url_prefix='/rooms')
        self.app.register_blueprint(bp_login)
        self._old_path = app.room_builder.map_source.dirpath
        app.room_builder.map_source.dirpath = os.path.join(
            os.path.dirname(__file__), "../test_maps")
        init_login(self.app)
        app.master.load_scripts("rooms.flask.app_test")
        app.container.room_script_name = "rooms.flask.app_test"
        app.container.player_script_name = "rooms.flask.app_test"
        app.node.start()

        self.client = self.app.test_client()

        self.app.add_url_rule("/", 'index', lambda: "Index")

        self.client.post('/register', data=dict(
            username='bob', password='pass'))
        self.client.post('/register', data=dict(
            username='ned', password='pass'))

    def tearDown(self):
        app.room_builder.map_source.dirpath = self._old_path

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_connect_to_game(self):
        game_id = app.master.create_game('bob')
        app.master.join_game(game_id, 'bob')

        self.login('bob', 'pass')
        res = self.client.get('/rooms/connect/games_0')
        self.assertEquals(200, res.status_code)
        self.assertEquals({"wait": 1}, json.loads(res.data.decode()))

        app.node.load_next_pending_room()

        res = self.client.get('/rooms/connect/games_0')
        self.assertEquals(200, res.status_code)
        data = json.loads(res.data.decode())
        self.assertTrue('actor_id' in data)
        self.assertEquals("localhost:5000", data['host'])
        self.assertEquals("http://localhost:5000/rooms/call/games_0",
                          data['call'])
        self.assertEquals("ws://localhost:5000/rooms/play/games_0",
                          data['connect'])

    def test_node_hostname(self):
        app.node.host = "node1.rooms.com"
        # restarting saves the node info into the db
        app.node.start()

        game_id = app.master.create_game('bob')
        app.master.join_game(game_id, 'bob')

        self.login('bob', 'pass')
        res = self.client.get('/rooms/connect/%s' % (game_id,))
        self.assertEquals(200, res.status_code)
        self.assertEquals({"wait": 1}, json.loads(res.data.decode()))

        app.node.load_next_pending_room()

        res = self.client.get('/rooms/connect/%s' % (game_id,))
        self.assertEquals(200, res.status_code)
        data = json.loads(res.data.decode())
        self.assertTrue('actor_id' in data)
        self.assertEquals("node1.rooms.com", data['host'])
        self.assertEquals("http://node1.rooms.com/rooms/call/games_0",
                          data['call'])
        self.assertEquals("ws://node1.rooms.com/rooms/play/games_0",
                          data['connect'])

    def test_has_not_joined(self):
        game_id = app.master.create_game('bob')
        self.login('bob', 'pass')
        res = self.client.get('/master/connect/1234')
        self.assertEquals(401, res.status_code)
