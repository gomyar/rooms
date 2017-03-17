
import flask_login
from flask_login import login_required
from flask import Blueprint
from flask import jsonify
from flask import send_from_directory
from flask import render_template
from flask import request

from rooms.flask import app
from rooms.flask.app import mapdir

import logging
log = logging.getLogger("rooms.flask.admin")

bp_admin = Blueprint('admin', __name__, template_folder='templates',
                     static_folder='static', url_prefix='/rooms_admin')


@bp_admin.route("/")
@login_required
def index():
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    return render_template('admin/index.html')


@bp_admin.route("/connect/<game_id>/<room_id>", methods=['GET', 'POST'])
@login_required
def admin_connects(game_id, room_id):
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    room = app.container.request_create_room(game_id, room_id)
    if room.get('node_name'):
        node_host = app.container.load_node(room['node_name']).host
        return jsonify({
            'host': node_host,
            'connect': "ws://%s/rooms_admin/view/%s/%s" % (node_host, game_id, room_id),
        })
    else:
        return jsonify({'wait': 1})


@bp_admin.route("/view/<game_id>/<room_id>")
def admin_view(game_id, room_id):
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    log.debug("Attempted ws connection")
    if flask_login.current_user.is_anonymous:
        log.debug("Anonymous user not allowed")
        return "Anonymous user not allowed", 401
    if not flask_login.current_user.is_admin():
        log.debug("Non-admin user cannot view")
        return "Non-admin user cannot view", 401
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        log.debug("Player %s connected to game %s",
            flask_login.current_user.get_id(), game_id)
        app.node.admin_connects(ws, game_id, room_id)
        log.debug("player %s disconnected from game %s",
            flask_login.current_user.get_id(), game_id)


@bp_admin.route("/nodes")
@login_required
def list_nodes():
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    nodes = [{'name': n.name, 'host': n.host, 'load': n.load,
             'uptime': n.uptime, 'healthy': n.healthy()} for n in
             app.container.list_nodes()]
    return jsonify(nodes)


@bp_admin.route("/rooms")
@login_required
def list_rooms():
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    active = request.args.get('active', True)
    node_name = request.args.get('node_name')
    game_id = request.args.get('game_id')
    rooms = app.container.list_rooms(
        active=active, node_name=node_name,
        game_id=game_id)
    return jsonify([{'game_id': r.game_id, 'room_id': r.room_id,
                     'node_name': r.node_name} for r in
                     rooms])


@bp_admin.route("/games")
@login_required
def list_games():
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    node_name = request.args.get('node_name')
    owner_id = request.args.get('owner_id')
    games = [{'game_id': g.game_id, 'owner_id': g.owner_id,
              'created_on': g.created_on} for g in
             app.container.list_games(owner_id, node_name)]
    return jsonify(games)


@bp_admin.route("/players")
@login_required
def list_players(node_name=None):
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    return jsonify(app.container.list_players(node_name))


@bp_admin.route('/maps/<path:path>')
@login_required
def get_map(path):
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    return send_from_directory(mapdir, path)
