#!/usr/bin/env python

import sys
import socket
from gevent import monkey
monkey.patch_all()

from flask import Flask
from flask import redirect
from flask import render_template
from flask import jsonify
from flask import request
from flask import send_from_directory

from rooms.flask.login import init_login
from rooms.flask.login import bp_login
from rooms.flask.master import bp_master
from rooms.flask.node import bp_node
from rooms.flask.admin import bp_admin
from rooms.flask.mapeditor import bp_mapeditor

from rooms.flask.app import master
from rooms.flask.app import node
from rooms.flask.app import start_rooms_app
from rooms.flask.app import mapdir

from flask_login import login_required
import flask_login


def create_app():
    app = Flask(__name__)
    app.secret_key = 'keepitsecretkeepitsafe'

    app.register_blueprint(bp_login)
    app.register_blueprint(bp_node)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_mapeditor)

    return app


app = create_app()


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/games")
@login_required
def games():
    return jsonify(master.list_all_games())


@app.route("/creategame", methods=['POST'])
@login_required
def create_game():
    return master.create_game(flask_login.current_user.get_id())


@app.route("/join/<game_id>", methods=['POST'])
@login_required
def join(game_id):
    # default implementation
    return jsonify(master.join_game(game_id, flask_login.current_user.get_id()))


@app.route("/play/<game_id>")
@login_required
def play(game_id):
    return render_template("game.html", game_id=game_id)


@app.route('/maps/<path:path>')
def get_map(path):
    return send_from_directory(mapdir, path)


if __name__ == '__main__':
    sys.path.append('./src')

    app.config['SESSION_COOKIE_DOMAIN'] = socket.gethostname()

    init_login(app)

    master.load_scripts('scripts.game_script')
    node.load_scripts('./scripts')
    node.start()

    start_rooms_app(app)
