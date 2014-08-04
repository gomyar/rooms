
var api_rooms = {};

api_rooms.server_time = 0;
api_rooms.local_time = 0;
api_rooms.token = "";

api_rooms.room = { topleft: {'x': 0, 'y': 0, 'z': 0}, bottomright: {'x': 0, 'y': 0, 'z': 0}, map_objects: [] };

api_rooms.actors = {};
api_rooms.socket = null;

api_rooms.master_url = "http://localhost:9999";


api_rooms.Actor = function(actor)
{
    for (key in actor)
        this[key] = actor[key];
}

api_rooms.Actor.prototype._calc_d = function(start_d, end_d)
{
    var now = api_rooms.get_now();
    var start_time = this.vector.start_time * 1000;
    var end_time = this.vector.end_time * 1000;
    if (now > end_time)
        return end_d;
    var diff_x = end_d - start_d;
    var diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_d;
    var inc = (now - start_time) / diff_t;
    return start_d + diff_x * inc;
}

api_rooms.Actor.prototype.x = function()
{
    return this._calc_d(this.vector.start_pos.x, this.vector.end_pos.x)
}

api_rooms.Actor.prototype.y = function()
{
    return this._calc_d(this.vector.start_pos.y, this.vector.end_pos.y)
}

api_rooms.Actor.prototype.z = function()
{
    return this._calc_d(this.vector.start_pos.z, this.vector.end_pos.z)
}

api_rooms.Actor.prototype.parent_actor = function()
{
    if (this.parent_id != null && this.parent_id in api_rooms.actors)
        return api_rooms.actors[this.parent_id];
    else
        return null;
}

api_rooms.Actor.prototype.atPosition = function(x, y)
{
    x1 = this.x() - this.width / 2;
    y1 = this.y() - this.height / 2;
    x2 = x1 + this.width;
    y2 = y1 + this.height;
    return x > x1 && x < x2 && y > y1 && y < y2;
}


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
//    data.token = api_rooms.token;
    $.ajax({
        'url': url,
        'data': data,
        'success': function(data) {
            if (callback != null)
                callback(data);
        },
        'error': function(jqXHR, errorText) {
            console.log("Error calling "+url+" : "+errorText);
        },
        'type': 'POST'
    });
}

api_rooms.onopen = function()
{
    console.log("Sending token: "+api_rooms.token);
    api_rooms.socket.send(api_rooms.token);
}

api_rooms.onclose = function()
{
    console.log("Connection lost");
}

api_rooms.connect = function(game_id, username, token, custom_callback)
{
    api_rooms.game_id = game_id;
    api_rooms.username = username;
    api_rooms.token = token;

    api_rooms.socket = new WebSocket("ws://"+window.location.hostname+":"+window.location.port+"/game/player_connects?game_id=" + game_id + "&username=" + username + "&token=" + token);
    api_rooms.socket.onmessage = api_rooms.message_callback;
    api_rooms.socket.onopen = api_rooms.onopen;
    api_rooms.socket.onclose = api_rooms.onclose;
    api_rooms.socket.onerror = api_rooms.onclose;

    api_rooms.custom_callback = custom_callback;

}

api_rooms.connect = function(username, game_id)
{
    api_rooms.service_call(api_rooms.master_url + "/player/player_connects",
        {"username": username, "game_id": game_id}, function(data) {
            api_rooms.init(data.node[0], data.node[1], data.token);
        });
}

api_rooms.admin_connect = function(host, port, token, custom_callback)
{
    console.log("Connecting to : "+ host + ":" + port + " " + token);
    api_rooms.actors = {};
    api_rooms.game_id = null;
    api_rooms.username = 'admin';
    api_rooms.token = token;

    api_rooms.socket = new WebSocket("ws://"+host+":"+port+"/node_game/admin_connects/"+token);
    api_rooms.socket.onmessage = api_rooms.message_callback;
    api_rooms.socket.onopen = api_rooms.onopen;
    api_rooms.socket.onclose = api_rooms.onclose;
    api_rooms.socket.onerror = api_rooms.onclose;

    api_rooms.custom_callback = custom_callback;

}


api_rooms.command_sync = function(message)
{
    api_rooms.set_now(message.data.now);
    api_rooms.load_room_map(message.data.room_id);
}

api_rooms.load_room_map = function(room_id)
{
    var map_id = room_id.split('.')[0];
    var room_key = room_id.split('.')[1];

    api_rooms.service_call(api_rooms.master_url + "/maps/" + map_id + ".json", {}, function(map_data){
        api_rooms.room = map_data.rooms[room_key];        
        api_rooms.custom_callback({
            "command": "map_loaded",
            "room_id": room_id,
            "map_id": map_id,
            "room_key": room_key,
            "map_data": map_data});
    });
}

api_rooms.command_actor_update = function(message)
{
    if (message.actor_id in api_rooms.actors)
    {
        for (var f in message.data)
            api_rooms.actors[message.actor_id][f] = message.data[f];
    }
    else
        api_rooms.actors[message.actor_id] = new api_rooms.Actor(message.data);
}

api_rooms.command_remove_actor = function(message)
{
    delete api_rooms.actors[message.actor_id];
}

api_rooms.command_moved_node = function(message)
{
    window.location = "http://"+message.node[0]+":"+message.node[1]+"/assets/index.html?token="+message.token+"&game_id="+api_rooms.game_id+"&username="+api_rooms.username;
}

api_rooms.commands = {
    "sync": api_rooms.command_sync,
    "actor_update": api_rooms.command_actor_update,
    "remove_actor": api_rooms.command_remove_actor,
    "redirect": api_rooms.command_moved_node
};

api_rooms.message_callback = function(msgevent)
{
    var message = jQuery.parseJSON(msgevent.data);
    if (message.command in api_rooms.commands)
        api_rooms.commands[message.command](message);
    if (api_rooms.custom_callback)
        api_rooms.custom_callback(message);
}


// *** API Calls
api_rooms.call_command = function(actor_id, command, args, callback)
{
    api_rooms.service_call("/game/actor_call/" + api_rooms.game_id + "/" + api_rooms.username + "/" + actor_id + "/" + api_rooms.token + "/" + command, args, callback);
}

api_rooms.actor_request = function(actor_id, command, args, callback)
{
    api_rooms.service_call("/actors/"+actor_id+"/"+command, args, callback)
}

api_rooms.actors_by_type = function()
{
    var actors = {};
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (!(actor.actor_type in actors))
            actors[actor.actor_type] = {};
        actors[actor.actor_type][actor.name + ": "+actor.actor_id] = actor;
    }
    return actors;
}

api_rooms.player_actors = function()
{
    var actors = [];
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (actor.username == api_rooms.username)
            actors[actors.length] = actor;
    }
    return actors;
}
