
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
            if (callback != null)
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
        gui.requestRedraw();
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
}

api_rooms.connect = function(message_callback)
{
    api_rooms.socket = new WebSocket("ws://"+window.location.hostname+":8080/socket");
    api_rooms.socket.onmessage = message_callback;
    api_rooms.socket.onopen = api_rooms.onopen;
    api_rooms.socket.onclose = api_rooms.onclose;
    api_rooms.socket.onerror = api_rooms.onclose;
}

// *** API Calls

api_rooms.leave_instance = function(callback)
{
    api_rooms.service_call("/game/" + api_rooms.instance_uid + "/" + api_rooms.player_id + "/leave_instance",
        { }, callback)
}

api_rooms.list_inventory = function(data_callback)
{
    api_rooms.service_call("/game/" + api_rooms.instance_uid + "/" + api_rooms.player_id + "/list_inventory",
        { }, data_callback)
}

api_rooms.exit_through_door = function(door_id)
{
    api_rooms.service_call("/game/" + api_rooms.instance_uid + "/" + api_rooms.player_id + "/exit",
        { "door_id": door_id })
}

api_rooms.walk_to = function(x, y)
{
    api_rooms.service_call("/game/"+api_rooms.instance_uid+"/"+api_rooms.player_id+"/move_to",
        { x : x, y : y });
}

api_rooms.exposed_commands = function(actor_id, data_callback)
{
    api_rooms.service_call("/game/" + api_rooms.instance_uid + "/" + actor_id + "/exposed_commands", {}, data_callback);
}

api_rooms.exposed_methods = function(actor_id, data_callback)
{
    api_rooms.service_call("/game/" + api_rooms.instance_uid + "/" + actor_id + "/exposed_methods", {}, data_callback);
}

api_rooms.chat = function(actor_id, choice_text, data_callback)
{
    api_rooms.service_call("/game/" + api_rooms.instance_uid + "/" + actor_id + "/chat", { "message": choice_text }, data_callback);
}
