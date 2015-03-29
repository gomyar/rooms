=====
rooms_jsclient
=====

Rooms JS Client basically just one file - api_rooms.js which is structured as a django app for ease of inclusion into django projects.

Note: It's also got some JQuery stuff in there, because it's a little dependent on jquery, and I'm fed up of copying jquery everywhere.

Quick start
-----------

1. Add "rooms_jsclient" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'rooms_jsclient',
      )

2. Include the rooms_jsclient static file, using the normal django staticfiles app::

3. Include the client in your app from http://127.0.0.1:8000/static/rooms_jsclient/js/api_rooms.js
