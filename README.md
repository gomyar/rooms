
Rooms.

A framework for creating networked games.

Note: this tool is in an Alpha state.

Rooms is meant to handle the loading and scaling of "rooms" for a game, and allows development of a game using simple scripts.
The service is stateful, with all of the game state running on the server. Updates are pushed to clients over websockets.
It uses an admin interface for real time viewing of ongoing games, and a mapeditor for the simple map structure the game uses.
Pluggable geographies may be used for pathfinding, including grid based and polygon funnel (over A*).
