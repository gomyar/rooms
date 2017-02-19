
import unittest
from flask import Flask
from rooms.flask.master import bp_master
from rooms.flask.node import bp_node
from rooms.flask.login import init_login
from rooms.flask.login import bp_login
from rooms.flask import app
from rooms.testutils import MockDbase



class FlaskAppTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        app.container.dbase = self.dbase
        self.app = Flask(__name__)
        self.app.secret_key = "1234test"
        self.app.register_blueprint(bp_master)
        self.app.register_blueprint(bp_node)
        self.app.register_blueprint(bp_login)
        init_login(self.app)

        self.client = self.app.test_client()

        self.app.add_url_rule("/", 'index', lambda: "Index")

        self.client.post('/register', data=dict(
            username='bob', password='pass'))
        self.client.post('/register', data=dict(
            username='ned', password='pass'))

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
        self.assertEquals('{\n  "wait": 1\n}\n', res.data)

        app.node.load_next_pending_room()

        res = self.client.get('/rooms/connect/games_0')
        self.assertEquals(302, res.status_code)
        self.assertEquals("http://localhost/play/games_0", res.headers['location'])

        # Check node host is reflected in the redirect
        app.node.host = "node1.rooms.com"

        res = self.client.get('/rooms/connect/1234')
        self.assertEquals(302, res.status_code)
        self.assertEquals("http://node1.rooms.com/play/1234", res.headers['location'])

    def test_has_not_joined(self):
        game_id = app.master.create_game('bob')
        self.login('bob', 'pass')
        res = self.client.get('/rooms/connect/1234')
        self.assertEquals(401, res.status_code)
