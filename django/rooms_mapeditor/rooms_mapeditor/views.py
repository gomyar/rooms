import os
import json

from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render_to_response
from django.http import HttpResponse

from django.conf import settings


def responsejson(func):
    def call(request, *args, **kwargs):
        return HttpResponse(json.dumps(func(request, *args, **kwargs)))
    return call


@permission_required("is_staff")
def index(request):
    return render_to_response("rooms_mapeditor/index.html")


@permission_required("is_staff")
@responsejson
def maps(request):
    map_root = getattr(settings, "ROOMS_MAP_ROOT", "maps")
    if request.method == 'POST':
        params = json.loads(request.body)
        map_id = params.get('map_id')
        if not map_id:
            raise Exception("No map_id")
        map_path = os.path.join(map_root, map_id + ".json")
        if os.path.exists(map_path):
            raise Exception("Map already exists")
        map_file = open(map_path, "w")
        map_file.write(json.dumps({"map_id": map_id,
            "rooms": {map_id + ".room1":
                {
                    "info": {},
                    "topleft": {"x": -10, "y": -10},
                    "bottomright": {"x": 10, "y": 10},
                    "tags": {},
                    "room_objects": {},
                    "doors": {},
                }
        }}))
        map_file.close()
    else:
        return [os.path.splitext(m)[0] for m in os.listdir(map_root)]


@permission_required("is_staff")
def load_map(request, map_id):
    map_root = getattr(settings, "ROOMS_MAP_ROOT", "maps")
    return HttpResponse(open(os.path.join(map_root, map_id + ".json")).read())
