from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
import xmlrpclib
from django.template import RequestContext
from django.conf import settings

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

master = xmlrpclib.ServerProxy(settings.MASTER_ADDR)

@login_required
def running_instances(request):
    user_id = request.user.pk
    instances = master.list_instances()
    own_instance = master.own_instance(str(user_id))
    if own_instance:
        instance = instances[own_instance]
        return HttpResponseRedirect(
            "http://%s:%s/?instance_uid=%s&player_id=%s" % \
            (instance['node'][0], instance['node'][1],
            own_instance, user_id))
    else:
        return render_to_response("list_instances.html",
            dict(instances=instances.values()),
            context_instance=RequestContext(request))

@login_required
def create_instance(request):
    user_id = request.user.pk
    map_id = request.POST['map_id']
    master.create_instance(str(user_id), map_id)
    return HttpResponseRedirect("/")

@login_required
def join_instance(request):
    user_id = request.user.pk
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
