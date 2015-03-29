from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms_mapeditor.views',
    url(r'^$', 'index', name='rooms_mapeditor_index'),
)
