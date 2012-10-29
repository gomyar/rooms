from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
import xmlrpclib
from django.template import RequestContext
from django.conf import settings

from pymongo import Connection
from pymongo.helpers import bson

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

master = xmlrpclib.ServerProxy(settings.MASTER_ADDR)

_mongo_connection = None

def get_mongo_conn():
    global _mongo_connection
    if not _mongo_connection:
        init_mongo()
    return _mongo_connection

def init_mongo(host='localhost', port=27017):
    global _mongo_connection
    _mongo_connection = Connection(host, port)


def list_all_areas_for(owner_id):
    rooms_db = get_mongo_conn().rooms_db
    areas = rooms_db.areas.find({ 'owner_id': owner_id }, fields=['area_name'])
    return map(lambda a: dict(area_name=a['area_name'], area_id=str(a['_id'])),
        areas)

def index(request):
    return render_to_response("index.html", dict(user=request.user),
        context_instance=RequestContext(request))

def profile(request):
    return HttpResponseRedirect("/")

@login_required
def running_instances(request):
    user_id = request.user.username
    instances = master.list_instances()
    own_instance = master.own_instance(str(user_id))
    if own_instance:
        instance = instances[own_instance]
        return HttpResponseRedirect(
            "http://%s:%s/?instance_uid=%s&player_id=%s" % \
            (instance['node'][0], instance['node'][1],
            own_instance, request.user.username))
    else:
        return render_to_response("list_instances.html",
            dict(instances=instances.values(),
            available_maps=list_all_areas_for(user_id)),
            context_instance=RequestContext(request))

@login_required
def create_instance(request):
    user_id = request.user.username
    map_id = request.POST['map_id']
    master.create_instance(str(user_id), map_id)
    return HttpResponseRedirect("/")

@login_required
def join_instance(request):
    user_id = request.user.username
    instance_uid = request.POST['instance_uid']
    log.debug("User %s joining %s", user_id, instance_uid)
    response = master.join_instance(str(user_id), instance_uid)
    if response['success']:
        return HttpResponseRedirect(
            "http://%s:%s/?instance_uid=%s&player_id=%s" % \
            (response['node'][0], response['node'][1],
            instance_uid, user_id))
    else:
        return HttpResponse("Unsuccessful")
