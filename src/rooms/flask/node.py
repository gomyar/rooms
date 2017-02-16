
import flask_login
from flask_login import login_required
from flask import Blueprint
from flask import request
from flask import redirect
from flask import jsonify

from rooms.flask import app

import logging
log = logging.getLogger("rooms.flask.node")

bp_node = Blueprint('node', __name__, template_folder='templates',
                    static_folder='static', url_prefix='/rooms')


@bp_node.route("/play/<game_id>")
def play(game_id):
    log.debug("attempting to connect to game %s", game_id)
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        log.debug("Player %s connected to game %s", flask_login.current_user.get_id(), game_id)
        app.node.player_connects(ws, game_id, flask_login.current_user.get_id())


@bp_node.route("/connect/<game_id>", methods=['GET', 'POST'])
@login_required
def connect(game_id):
    # get player for game_id / user_id
    player = app.container.get_player(game_id, flask_login.current_user.get_id())
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


@bp_node.route("/actor_call/<game_id>/<method>")
@login_required
def actor_call(game_id, method):
    return app.node.actor_call(game_id, method)


@bp_node.route("/admin_connects/<game_id>")
@login_required
def admin_connects(game_id):
    if flask_login.current_user.is_admin():
        pass
