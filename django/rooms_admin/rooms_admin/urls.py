from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms_admin.views',
    url(r'^$', 'index', name='rooms_admin_index'),

    url(r'^all_nodes', 'all_nodes', name='rooms_all_nodes'),
)
