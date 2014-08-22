
var image_map = {
    'player': '/static/rooms_demo/images/character_models/player.png',
    'npc': '/static/rooms_demo/images/character_models/npc.png'
}
var rootVars = null;

perform_get = function(url, callback, onerror)
{
    $.ajax({
        'url': url,
        'success': function(data) {
            if (callback != null)
                callback(data);
        },
        'error': function(jqXHR, errorText) {
            console.log("Error calling "+url+" : "+errorText);
            if (onerror)
                onerror(errorText, jqXHR);
        },
        'type': 'GET'
    });
}


function init_game(game_id, username)
{
    console.log("Loading images");
    guiassets.loadImages(image_map, function() {
        console.log("Loaded images");

        gui.initCanvas($("#screen")[0]);

        $("#screen").click(canvas_clicked);
        $("#screen").mousemove(canvas_mousemove);
        api_rooms.connect("http://" + window.location.hostname +":"+ window.location.port +"/rooms_demo", game_id, username, api_callback);

        $(window).bind('beforeunload', function(){
            api_rooms.socket.close();
        });
    });
}


canvas_clicked = function(e)
{
    var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
    var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));
    console.log("clicked "+click_x+","+click_y);

    var player_actor = api_rooms.player_actors()[0];
    if (gui.door_hovered)
        api_rooms.call_command(player_actor.actor_id, "exit_through_door", { exit_room_id: gui.door_hovered.exit_room_id });
    else
        api_rooms.call_command(player_actor.actor_id, "move_to", { x: click_x, y: click_y });
}


canvas_mousemove = function(e)
{
    var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
    var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));

    gui.actor_hovered = gui_actors.actor_at(click_x, click_y);
    gui.door_hovered = gui_room.door_at(click_x, click_y);

    if (gui.door_hovered || gui.actor_hovered)
        $(gui.canvas).css('cursor', 'pointer');
    else
        $(gui.canvas).css('cursor', 'auto');

    gui.debug.mouse_at = [click_x, click_y];
    gui.requestRedraw();
}


function api_callback(message)
{
    console.log("API Message:");
    console.log(message);
    gui.actorRedraw();
    if (message.command == "actor_update")
    {
        var player_actors = api_rooms.player_actors();
        if (player_actors.length > 0)
        {
            gui.following_actor = player_actors[0];
            var scope = angular.element($("#logwindow")).scope();
            scope.$apply(function() {
                scope.logmessages = gui.following_actor.state.log;
            });
        }
        gui.requestRedraw();
    }
    if (message.command == "sync")
    {
        api_rooms.actors = {};
        load_room(message.data.room_id);
        gui.requestRedraw();
    }
}

function load_room(room_id)
{
    var map_id = room_id.split('.')[0];
    var map_room_id = room_id.split('.')[1];

    perform_get("/static/rooms_demo/maps/" + map_id + ".json",
        function(data){ show_room(data, map_room_id);},
        function(errTxt, jqXHR){ alert("Error loading room: "+errTxt);});
}

function show_room(data, map_room_id)
{
    api_rooms.room = data['rooms'][map_room_id];
    gui.requestRedraw();
}


