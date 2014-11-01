from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms_admin.views',
    url(r'^$', 'index', name='rooms_admin_index'),

    url(r'^all_nodes', 'all_nodes', name='rooms_all_nodes'),
    url(r'^all_rooms_on_node/(?P<host>[\w]*)/(?P<port>[\w]*)', 'all_rooms_on_node', name='rooms_all_rooms_on_node'),
    url(r'^request_admin_token', 'request_admin_token', name='rooms_request_admin_token'),
    url(r'^all_items', 'all_items', name='rooms_all_items'),
    url(r'^save_item', 'save_item', name='rooms_save_item'),
)
