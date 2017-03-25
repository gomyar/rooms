
from os import path
import json

import flask_login
from flask_login import login_required
from flask import Blueprint
from flask import request
from flask import redirect
from flask import jsonify

from rooms.flask import app

import logging
log = logging.getLogger("rooms.flask.node")

bp_node = Blueprint('node', __name__,
                    template_folder=path.join(
                        path.dirname(__file__), 'templates'),
                    static_folder=path.join(
                        path.dirname(__file__), 'static/rooms'),
                    static_url_path='/static',
                    url_prefix='/rooms')


@bp_node.route("/play/<game_id>")
def play(game_id):
    log.debug("Attempted ws connection")
    if flask_login.current_user.is_anonymous:
        log.debug("Anonymous user not allowed")
        return "Anonymous user not allowed", 401
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        log.debug("Player %s connected to game %s",
                  flask_login.current_user.get_id(), game_id)
        app.node.player_connects(ws, game_id,
                                 flask_login.current_user.get_id())
        log.debug("player %s disconnected from game %s",
                  flask_login.current_user.get_id(), game_id)
    return "closed"


@bp_node.route("/connect/<game_id>", methods=['GET', 'POST'])
@login_required
def connect(game_id):
    # get player for game_id / user_id
    player = app.container.get_player(
        game_id, flask_login.current_user.get_id())
    # redirect to / request associated node
    room = app.container.request_create_room(game_id, player['room_id'])
    if room.get('node_name'):
        node_host = app.container.load_node(room['node_name']).host
        return jsonify({
            'host': node_host,
            'connect': "ws://%s/rooms/play/%s" % (node_host, game_id),
            'call': "http://%s/rooms/call/%s" % (node_host, game_id),
            'actor_id': player['actor_id']})
    else:
        return jsonify({'wait': 1})


@bp_node.route("/call/<game_id>", methods=['POST'])
@login_required
def actor_call(game_id):
    method = request.values['method']
    actor_id = request.values['actor_id']
    params = json.loads(request.values['params'])
    log.debug("Calling %s -> %s", actor_id, method)
    return jsonify(app.node.actor_call(
        game_id, flask_login.current_user.get_id(),
        actor_id, method, **params))


@bp_node.route("/healthcheck")
def healthcheck():
    if app.node.active:
        return '{"active": true}', 200
    else:
        return '{"active": false}', 503
