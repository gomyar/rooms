
import flask
from flask_login import login_required
from flask import Blueprint

bp_master = Blueprint('master', __name__, template_folder='templates',
                      static_folder='static')


@bp_master.route("/join_game/<game_id>")
@login_required
def join_game(game_id):
    # do join game
    #   create_or_get_player for game
    # redirect to correct node
    # get node for player room_id, redirect
    return flask.redirect(flask.url_for('node.play', game_id=game_id))


@bp_master.route("/join_game/<game_id>")
@login_required
def connect(game_id):
    # lookup game
    # redirect to correct node
    return flask.redirect(flask.url_for('node.play', game_id=game_id))
