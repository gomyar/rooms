from django.conf.urls.defaults import *

urlpatterns = patterns('game.views',
    (r'^$', 'index'),
    (r'^running_instances$', 'running_instances'),
    (r'^create_instance$', 'create_instance'),
    (r'^join_instance$', 'join_instance'),
)
