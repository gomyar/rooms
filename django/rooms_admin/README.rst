=====
rooms_admin
=====

Rooms Admin is a Django frontend for administration and debugging of a Rooms server.

Quick start
-----------

1. Add "rooms_admin" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'rooms_admin',
      )

2. Include the rooms_admin URLconf in your project urls.py like this::

      url(r'^rooms_admin/', include('rooms_admin.urls')),

3. Browse to http://127.0.0.1:8000/rooms_admin/ to view active games on the server
