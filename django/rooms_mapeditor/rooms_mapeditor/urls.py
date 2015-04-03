from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms_mapeditor.views',
    url(r'^$', 'index', name='rooms_mapeditor_index'),
    url(r'^maps$', 'maps', name='rooms_mapeditor_maps'),
    url(r'^maps/(?P<map_id>[\w\.]*)$', 'load_map', name='rooms_mapeditor_load_map'),
)
