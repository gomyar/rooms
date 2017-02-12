
import flask
import flask_login
from flask_login import login_required
from flask import Blueprint

from rooms.flask import app

bp_master = Blueprint('master', __name__, template_folder='templates',
                      static_folder='static', url_prefix='/master')


@bp_master.route("/connect/<game_id>")
@login_required
def connect(game_id):
    # lookup game
    player = app.container.get_player(game_id, flask_login.current_user.get_id())
    # redirect to / request associated node
    if not player:
        return "User has not joined game", 401
    room = app.container.request_create_room(game_id, player['room_id'])
    if room.get('node_name'):
        return flask.redirect(flask.url_for('node.play', game_id=game_id))
    else:
        return "Room not ready", 503
