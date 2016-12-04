
from flask_login import login_required
from flask import Blueprint

bp_node = Blueprint('node', __name__, template_folder='templates',
                    static_folder='static')


@bp_node.route("/play/<game_id>")
@login_required
def play(game_id):
    return "Connected!"
