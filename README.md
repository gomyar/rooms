
Rooms.

A framework for creating networked games.

Note: this tool is in an Alpha state.

Rooms is meant to handle the loading and scaling of "rooms" for a game, and allows development of a game using simple scripts.
The service is stateful, with all of the game state running on the server. Updates are pushed to clients over websockets.
It uses an admin interface for real time viewing of ongoing games, and a mapeditor for the simple map structure the game uses.
Pluggable geographies may be used for pathfinding, including grid based and polygon funnel (over A*).


Quickest way to get running demo.

In the demo/walkabout dir
 - run ./build.sh (just builds the docker image)
 - run ./debug.sh (runs a debug version using docker-compose)
 - navigate to localhost:5000/register 
 - add a user
 - navigate to localhost:5000
 - create a new game, join, click about etc.
 - then go here: localhost:5000/rooms_admin
 - then go here: localhost:5000/rooms_mapeditor
