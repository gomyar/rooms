
var current_map_id = null;
var current_map = null;

canvas_clicked = function(e)
{
    var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
    var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));
    console.log("clicked "+click_x+","+click_y);

    var player_actor = api_rooms.player_actor;
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

function load_room(room_id)
{
    var map_id = room_id.split('.')[0];
    var map_room_id = room_id.split('.')[1];

    if (map_id != current_map_id) {
        net.perform_get("/maps/" + map_id + ".json",
            function(data){ map_loaded(data, room_id);},
            function(errTxt, jqXHR){ alert("Error loading room: "+errTxt);});
    } else {
        show_room(room_id);
    }
}

function map_loaded(data, room_id)
{
    current_map = data;
    show_room(room_id);
}

function show_room(room_id)
{
    console.log("Showing room " + room_id);
    api_rooms.room = current_map['rooms'][room_id];
    gui.following_actor = api_rooms.player_actor;
    gui.requestRedraw();
}

function api_callback(message)
{
    console.log("API Message:");
    console.log(message);
    gui.actorRedraw();
    if (message.command == "actor_update")
    {
        gui.requestRedraw();
    }
    if (message.command == "sync")
    {
        api_rooms.actors = {};
        load_room(message.data.room_id);
        gui.requestRedraw();
    }
}

function init_game(game_id)
{
    console.log("Loaded images");

    gui.initCanvas($("#screen")[0]);

    gui.canvas.width = $("#main").width();
    gui.canvas.height = $("#main").height();

    $("#screen").click(canvas_clicked);
    $("#screen").mousemove(canvas_mousemove);
    api_rooms.connect("/rooms/connect/" + game_id, api_callback); 

    $(window).bind('beforeunload', function(){
        api_rooms.socket.close();
    });
}

$(document).ready(function() {
    console.log("initing");
    init_game(game_id);
});

