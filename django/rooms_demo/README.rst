=====
rooms_demo
=====

This is a Demo Game app for django.

Quick start
-----------

1. Add "rooms_demo" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'rooms_demo',
      )

2. Include the rooms_demo URLconf in your project urls.py like this::

      url(r'^rooms_demo/', include('rooms_demo.urls')),

3. Browse to http://127.0.0.1:8000/rooms_demo/ to view active games on the server
