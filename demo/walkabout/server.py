#!/usr/bin/env python

import sys
import socket
import gevent
from gevent import monkey
monkey.patch_all()

from flask import Flask
from flask import redirect
from flask import render_template
from flask import jsonify
from flask import request
from flask import send_from_directory

from flask_socketio import SocketIO, emit

from rooms.flask.login import init_login
from rooms.flask.login import bp_login
from rooms.flask.master import bp_master
from rooms.flask.node import bp_node
from rooms.flask.admin import bp_admin
from rooms.flask.mapeditor import bp_mapeditor

from rooms.flask.app import master
from rooms.flask.app import node
from rooms.flask.app import mapdir
from rooms.flask.app import GEOGRAPHIES
from rooms.flask.app import container
from rooms.flask.app import _node_host
from rooms.flask.app import _node_port

from rooms.node import SocketConnection

from flask_login import login_required
import flask_login

import logging
log = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.secret_key = 'keepitsecretkeepitsafe'

    app.register_blueprint(bp_login)
    app.register_blueprint(bp_node, url_prefix='/rooms')
    app.register_blueprint(bp_admin, url_prefix='/rooms_admin')
    app.register_blueprint(bp_mapeditor, url_prefix='/rooms_mapeditor')

    return app


app = create_app()
socketio = SocketIO(app, async_mode='gevent')


socket_map = {}


@login_required
@socketio.on('connect')
def on_connect():
    log.debug("Connected %s %s", flask_login.current_user.username, request.sid)


@login_required
@socketio.on('join_game')
def join_game(data):
    log.debug("Joining game %s %s %s %s %s", data['game_id'], flask_login.current_user.username, request.sid, data['connect_as_admin'], data.get('room_id'))
    connection = SocketConnection(node, data['game_id'], flask_login.current_user.username, socketio, request.sid, data['connect_as_admin'], data.get('room_id'))

    gthread = gevent.spawn(connection.connect_socket)

    socket_map[request.sid] = {"connection": connection, "gthread": gthread}


@login_required
@socketio.on('disconnect')
def on_disconnect():
    log.debug('Client disconnected %s', flask_login.current_user.username)
    connection = socket_map.pop(request.sid)
    connection['connection'].connected = False
    connection['connection'].queue.put({'command': 'disconnected_from_socket'})


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


def start_rooms_app(app, container_type='pointmap'):
    try:
        container.geography = GEOGRAPHIES[container_type]
        container.start_container()

        socketio.run(
            app,
            host=_node_host,
            port=_node_port)

    except KeyboardInterrupt as ke:
        log.debug("Server interrupted")
        node.shutdown()
        master.shutdown()
        container.stop_container()
    except:
        log.exception("Exception starting server")


if __name__ == '__main__':
    init_login(app)

    master.load_scripts('scripts.game_script')
    print(" --- Loading scripts into node at: %s", id(node))
    node.load_scripts('./scripts')
    node.start()

    start_rooms_app(app, "polygon_funnel")
