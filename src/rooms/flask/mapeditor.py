
import os
import json

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
log = logging.getLogger("rooms.flask.mapeditor")

bp_mapeditor = Blueprint('mapeditor', __name__,
                     template_folder=os.path.join(
                        os.path.dirname(__file__), 'templates'),
                     static_folder=os.path.join(
                        os.path.dirname(__file__), 'static/rooms_mapeditor'),
                     static_url_path='/static/rooms_mapeditor')


@bp_mapeditor.route("/")
@login_required
def index():
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    return render_template('rooms_mapeditor/mapeditor.html')



@bp_mapeditor.route('/maps', methods=['GET', 'POST', 'PUT'])
@login_required
def maps():
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    if request.method == 'POST':
        params = json.loads(request.data)
        map_id = params.get('map_id')
        if not map_id:
            raise Exception("No map_id")
        map_path = os.path.join(mapdir, map_id + ".json")
        if os.path.exists(map_path):
            raise Exception("Map already exists")
        map_file = open(map_path, "w")
        map_file.write(json.dumps({"map_id": map_id,
            "rooms": {map_id + ".room1":
                {
                    "info": {},
                    "position": {"x": 0, "y": 0},
                    "width": 10,
                    "height": 10,
                    "tags": [],
                    "room_objects": [],
                    "doors": [],
                }
        }}, indent=4))
        map_file.close()
        return jsonify({'result': 'ok'})
    if request.method == 'PUT':
        params = json.loads(request.data)
        map_data = params['map_data']
        map_id = map_data.get('map_id')
        map_path = os.path.join(mapdir, map_id + ".json")
        if not os.path.exists(map_path):
            raise Exception("Map does not exist")
        map_file = open(map_path, "w")
        map_file.write(json.dumps(map_data, indent=4))
        map_file.close()
        return jsonify({'result': 'ok'})
    else:
        return jsonify([os.path.splitext(m)[0] for m in os.listdir(mapdir)])


@bp_mapeditor.route('/maps/<path:path>')
@login_required
def get_map(path):
    if not flask_login.current_user.is_admin():
        return "Unauthorized", 401
    return send_from_directory(mapdir, path + '.json')
