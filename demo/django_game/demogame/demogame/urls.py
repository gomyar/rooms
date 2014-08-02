from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from django.contrib.auth.views import login
from django.contrib.auth.views import logout_then_login

import rooms_admin


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'demogame.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^rooms_admin/', include('rooms_admin.urls')),

    url(r'^accounts/login/$', login, name='account_login'),
    url(r'^accounts/logout/$', logout_then_login, name='account_logout'),
    url(r'^accounts/signup/$', "signup", name="account_signup"),
)
