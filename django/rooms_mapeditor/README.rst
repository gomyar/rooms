=====
rooms_mapeditor
=====

Rooms Map Editor is a Django for editing Rooms maps. It deals only with the base rooms models.

Quick start
-----------

1. Add "rooms_mapeditor" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'rooms_mapeditor',
      )

2. Include the rooms_mapeditor URLconf in your project urls.py like this::

      url(r'^rooms_mapeditor', include('rooms_mapeditor.urls')),

3. Browse to http://127.0.0.1:8000/rooms_mapeditor to use the app
