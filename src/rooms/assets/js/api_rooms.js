
var api_rooms = {};

api_rooms.server_time = 0;
api_rooms.local_time = 0;
api_rooms.token = "";

api_rooms.room = { width: 500, height: 500, position: [0, 0], map_objects: [], visibility_grid: { width : 0, height : 0, gridsize: 10 } };

api_rooms.actors = {};
api_rooms.player_actor = null;
api_rooms.socket = null;

api_rooms.facing_directions = {
    'north': Math.PI / 2,
    'south': Math.PI + Math.PI / 2,
    'east': Math.PI,
    'west': 0
};


api_rooms.Actor = function(actor)
{
    for (key in actor)
        this[key] = actor[key];
}

api_rooms.Actor.prototype.end_time = function()
{
    return this.path[this.path.length-1][2] * 1000;
}

api_rooms.Actor.prototype.x = function()
{
    now = api_rooms.get_now();
    if (now > this.end_time())
        return this.path[this.path.length-1][0];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    start_x = this.path[index][0];
    start_y = this.path[index][1];
    start_time = this.path[index][2] * 1000;
    end_x = this.path[index + 1][0];
    end_y = this.path[index + 1][1];
    end_time = this.path[index + 1][2]* 1000;

    now = api_rooms.get_now();
    if (now > end_time)
        return end_x;
    diff_x = end_x - start_x;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_x;
    inc = (now - start_time) / diff_t;
    return start_x + diff_x * inc;
}

api_rooms.Actor.prototype.y = function()
{
    now = api_rooms.get_now();
    if (now > this.end_time())
        return this.path[this.path.length-1][1];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    start_x = this.path[index][0];
    start_y = this.path[index][1];
    start_time = this.path[index][2] * 1000;
    end_x = this.path[index + 1][0];
    end_y = this.path[index + 1][1];
    end_time = this.path[index + 1][2]* 1000;

    now = api_rooms.get_now();
    if (now > end_time)
        return end_y;
    diff_y = end_y - start_y;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_y;
    inc = (now - start_time) / diff_t;
    return start_y + diff_y * inc;
}

api_rooms.Actor.prototype.parent_actor = function()
{
    if (this.parent_id != null && this.parent_id in api_rooms.actors)
        return api_rooms.actors[this.parent_id];
    else
        return null;
}

api_rooms.get_now = function()
{
    var local_now = new Date().getTime();
    var ticks = local_now - api_rooms.local_time;
    return ticks + api_rooms.server_time;
}

api_rooms.player_connection_to = function(actor)
{
    if (actor.circle_id == api_rooms.player_actor.circle_id)
        return "ally";
    if (actor.circle_id in api_rooms.player_actor.circles)
    {
        var friendship = api_rooms.player_actor.circles[actor.circle_id];
        if (friendship > 0)
            return "friend";
        else if (friendship < 0)
            return "enemy";
    }
    return "neutral";
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

api_rooms.load_room = function(callback)
{
    jQuery.get('/room/', function(data) {
        api_rooms.room = jQuery.parseJSON(data);
        if (callback)
            callback(data);
        gui.requestRedraw();
    });
}

api_rooms.onopen = function()
{
    api_rooms.socket.send(api_rooms.token);
}

api_rooms.onclose = function()
{
    console.log("Connection lost");
}

api_rooms.connect = function(deprecated_callback)
{
    api_rooms.socket = new WebSocket("ws://"+window.location.hostname+":"+window.location.port+"/socket");
    api_rooms.socket.onmessage = api_rooms.message_callback;
    api_rooms.socket.onopen = api_rooms.onopen;
    api_rooms.socket.onclose = api_rooms.onclose;
    api_rooms.socket.onerror = api_rooms.onclose;

    api_rooms.deprecated_callback = deprecated_callback;
}

api_rooms.command_sync = function(data)
{
    api_rooms.set_now(data.now);

    api_rooms.player_actor = new api_rooms.Actor(data.player_actor);

    api_rooms.actors = {};
    for (var i in data.actors)
    {
        var actor = data.actors[i];
        api_rooms.actors[actor.actor_id] = new api_rooms.Actor(actor);
    }
}

api_rooms.command_actor_update = function(data)
{
    if (data.actor_id == api_rooms.player_actor.actor_id)
        api_rooms.player_actor = new api_rooms.Actor(data);
    else if ("docked_with" in data && data.docked_with == api_rooms.player_actor.actor_id)
        api_rooms.player_actor.docked_actors[data.actor_type][data.actor_id] = data;
    else
        api_rooms.actors[data.actor_id] = new api_rooms.Actor(data);
}

api_rooms.command_remove_actor = function(data)
{
    console.log(" --- removing actor "+data.actor_id);
    if (data.actor_id != api_rooms.player_actor.actor_id)
        delete api_rooms.actors[data.actor_id];
}

api_rooms.command_moved_node = function(data)
{
    window.location = "http://"+data.host+":"+data.port+"/?token="+data.token;
}

api_rooms.commands = {
    "sync": api_rooms.command_sync,
    "actor_update": api_rooms.command_actor_update,
    "remove_actor": api_rooms.command_remove_actor,
    "moved_node": api_rooms.command_moved_node
};

api_rooms.message_callback = function(msg)
{
    var messages = jQuery.parseJSON(msg.data);
    for (var i in messages)
    {
        var message = messages[i];
        if (message.command in api_rooms.commands)
        {
            api_rooms.commands[message.command](message.kwargs);
        }
    }
    api_rooms.deprecated_callback(msg);
}


// *** API Calls
api_rooms.call_command = function(command, args, callback)
{
    api_rooms.service_call("/game/"+command, args, callback)
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
