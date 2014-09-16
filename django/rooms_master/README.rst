=====
rooms_master
=====

Rooms Master is a Django app which acts as an intermediary between a django project and rooms' master service. Mainly, it's for ensuring django authentication is used to send the "username" parameter to master calls. A rooms client should use this apps' views to perform master calls like joining and connecting to games.

Quick start
-----------

1. Add "rooms_master" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'rooms_master',
      )

2. Include the rooms_master URLconf in your project urls.py like this::

      url(r'^rooms_master/', include('rooms_master.urls')),

3. Browse to http://127.0.0.1:8000/rooms_master/ to view active games on the server
