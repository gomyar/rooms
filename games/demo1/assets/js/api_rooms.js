
var api_rooms = {};

api_rooms.server_time = 0;
api_rooms.local_time = 0;
api_rooms.instance_uid = "";
api_rooms.player_id = "";

api_rooms.room = { width: 500, height: 500, position: [0, 0], map_objects: [] };

api_rooms.actors = [];
api_rooms.own_actor = null;
api_rooms.socket = null;

api_rooms.facing_directions = {
    'north': Math.PI / 2,
    'south': Math.PI + Math.PI / 2,
    'east': Math.PI,
    'west': 0
};


api_rooms.command_chat = function ()
{
    api_rooms.service_call("/game/" + api_rooms.instance_uid + "/" + gui_game.selected_sprite.id + "/chat", {}, gui_screens.show_chat_window);
}

api_rooms.command_lookup = {
    "chat": api_rooms.command_chat,
};

api_rooms.get_now = function()
{
    var local_now = new Date().getTime();
    var ticks = local_now - api_rooms.local_time;
    return ticks + api_rooms.server_time;
}

api_rooms.set_now = function(now_time)
{
    api_rooms.server_time = now_time * 1000;
    api_rooms.local_time = new Date().getTime();
    gui.redraw_until = api_rooms.get_now();
    console.log("Server time : "+new Date(api_rooms.server_time));
    console.log("Local time : "+new Date(api_rooms.local_time));
}

api_rooms.service_call = function(url, data, callback)
{
    $.ajax({
        'url': url,
        'data': data,
        'success': function(data) {
            callback(jQuery.parseJSON(data));
        },
        'error': function(jqXHR, errorText) {
            console.log("Error calling "+url+" : "+errorText);
        },
        'type': 'POST'
    });
}

api_rooms.load_map = function(map_url)
{
    jQuery.get(map_url, function(data) {
        api_rooms.room = jQuery.parseJSON(data);
        for (i in api_rooms.room.map_objects)
        {
            var map_object = api_rooms.room.map_objects[i];
            map_object.img = images[map_object.object_type];
        }
    });
}

api_rooms.onopen = function()
{
    console.log("Connected with + player_id="+api_rooms.player_id+" instance_uid="+api_rooms.instance_uid);
    api_rooms.socket.send(api_rooms.player_id);
    api_rooms.socket.send(api_rooms.instance_uid);
}

api_rooms.onclose = function()
{
    console.log("Connection lost");
//    window.location = "http://localhost:8000";
}


