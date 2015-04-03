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
    return os.listdir(map_root)


@permission_required("is_staff")
def load_map(request, map_id):
    map_root = getattr(settings, "ROOMS_MAP_ROOT", "maps")
    return HttpResponse(open(os.path.join(map_root, map_id)).read())
