
var api_rooms = {};

api_rooms.server_time = 0;
api_rooms.local_time = 0;
api_rooms.token = "";
api_rooms.username = "";
api_rooms.player_actor = {"actor_id": "admin"};

api_rooms.actors = {};
api_rooms.socket = null;

api_rooms.game_id = null;
api_rooms.node_host = location.hostname;

api_rooms.conn_retries = 0;
api_rooms.max_retries = 3;
api_rooms.connecting = false;


api_rooms.Actor = function(actor)
{
    for (key in actor)
        this[key] = actor[key];
}

api_rooms.Actor.prototype._calc_d = function(start_d, end_d, start_t, end_t)
{
    var now = api_rooms.get_now();
    var start_time = start_t * 1000;
    var end_time = end_t * 1000;
    if (now > end_time)
        return end_d;
    var diff_x = end_d - start_d;
    var diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_d;
    var inc = (now - start_time) / diff_t;
    return start_d + diff_x * inc;
}

api_rooms.Actor.prototype.vector = function()
{
    if (this.parent_actor())
        return this.parent_actor().vector();
    var now = api_rooms.get_now();
    for (var v in this.path) {
        var vector = this.path[v];
        if (now >= vector.start_time * 1000 && now <= vector.end_time * 1000) {
            return vector;
        }
    }
    if (this.path) {
        return this.path[this.path.length-1];
    }
}

api_rooms.Actor.prototype.x = function()
{
    var vector = this.vector();
    return this._calc_d(vector.start_pos.x, vector.end_pos.x, vector.start_time, vector.end_time)
}

api_rooms.Actor.prototype.y = function()
{
    var vector = this.vector();
    return this._calc_d(vector.start_pos.y, vector.end_pos.y, vector.start_time, vector.end_time)
}

api_rooms.Actor.prototype.z = function()
{
    var vector = this.vector();
    return this._calc_d(vector.start_pos.z, vector.end_pos.z, vector.start_time, vector.end_time)
}

api_rooms.Actor.prototype.parent_actor = function()
{
    if (this.docked_with != null && this.docked_with in api_rooms.actors)
        return api_rooms.actors[this.docked_with];
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


api_rooms.Actor.prototype.docked = function(actor_type)
{
    var docked = [];
    for (var actor_id in api_rooms.actors)
    {
        var actor = api_rooms.actors[actor_id];
        if (actor.docked_with == this.actor_id && actor_type && actor.actor_type == actor_type)
            docked[docked.length] = actor;
    }
    return docked;
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
                callback(data);
        },
        'error': function(jqXHR, errorText) {
            console.log("Error calling "+url+" : "+errorText);
        },
        'type': 'POST',
        'xhrFields': { 
            'withCredentials': true 
        },
        'crossDomain': true
    });
}

api_rooms.onopen = function()
{
    console.log("Opened connection");
}

api_rooms.onclose = function()
{
    console.log("Connection closed");
}

api_rooms.onerror = function()
{
    console.log("Connection error");
}

api_rooms.connect = function(game_id, callback)
{
    api_rooms.connect_url = "/rooms/connect/" + game_id;
    api_rooms.game_id = game_id;
    api_rooms.game_callback = callback;

    api_rooms.request_connection();
}

api_rooms.request_connection = function()
{
    console.log("Requesting connection");
    api_rooms.connecting = true;
    //api_rooms.game_callback({'command': 'notify_connecting'});

    api_rooms.service_call(api_rooms.connect_url, {},
            function(data) {
                if ('wait' in data) {
                    if (api_rooms.conn_retries < api_rooms.max_retries) {
                        console.log("Waiting 1 second for room ready");
                        setTimeout(api_rooms.request_connection, 1000);
                        api_rooms.conn_retries += 1;
                    } else {
                        console.log("Connection Timed out");
                    }
                } else {
                    api_rooms.conn_retries = 0;
                    api_rooms.connecting = false;
                    api_rooms.websocket_url = data.connect;
                    api_rooms.call_url = data.call;
                    api_rooms.connect_node();
                }
            }
        );
}

api_rooms.connect_node = function()
{
    console.log("Connecting to Node " + api_rooms.node_host);

    api_rooms.socket = io(location.host, {transports: ["websocket", "polling"]});

    api_rooms.socket.on('connect', () => {
        console.log('Connected');
        api_rooms.socket.emit('join_game', {'game_id': api_rooms.game_id});
    });
    api_rooms.socket.on('disconnect', () => {
        console.log('Disconnected');
    });

    api_rooms.socket.on("sync", api_rooms.command_sync);
    api_rooms.socket.on("actor_update", api_rooms.command_actor_update);
    api_rooms.socket.on("remove_actor", api_rooms.command_remove_actor);
    api_rooms.socket.on("redirect_to_master", api_rooms.request_connection);

    api_rooms.game_callback();
}

api_rooms.command_sync = function(message)
{
    message = JSON.parse(message);
    console.log('Sync: ', message);
    api_rooms.actors = {};
    api_rooms.set_now(message.data.now);
    api_rooms.username = message.data.username;
    if (message.data.player_actor)
    {
        api_rooms.player_actor = new api_rooms.Actor(message.data.player_actor);
        api_rooms.actors[api_rooms.player_actor.actor_id] = api_rooms.player_actor;
    }
}


api_rooms.command_actor_update = function(message)
{
    message = JSON.parse(message);
    console.log('Actor update: ', message);
    if (message.actor_id == api_rooms.player_actor.actor_id)
    {
        for (var f in message.data)
            api_rooms.player_actor[f] = message.data[f];
    }
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
    message = JSON.parse(message);
    delete api_rooms.actors[message.actor_id];
}

api_rooms.commands = {
    "sync": api_rooms.command_sync,
    "actor_update": api_rooms.command_actor_update,
    "remove_actor": api_rooms.command_remove_actor,
    "redirect_to_master": api_rooms.request_connection
};

api_rooms.message_callback = function(msgevent)
{
    // Resetting retries as the open() function gets called anyway
    api_rooms.conn_retries = 0;
//    if (api_rooms.connecting) {
//        api_rooms.game_callback({'command': 'notify_connected'});
//    }

    var message = jQuery.parseJSON(msgevent.data);
    if (message.command in api_rooms.commands)
        api_rooms.commands[message.command](message);
//    if (api_rooms.game_callback)
//        api_rooms.game_callback(message);
}


// *** API Calls
api_rooms.call_command = function(actor_id, command, args, callback)
{
    var data = {
        'actor_id': actor_id,
        'method': command,
        'params': JSON.stringify(args)
    }
    api_rooms.service_call(api_rooms.call_url, data, callback);
}

api_rooms.actors_by_type = function()
{
    var actors = {};
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (!(actor.actor_type in actors))
            actors[actor.actor_type] = [];
        actors[actor.actor_type][actors[actor.actor_type].length] = actor;
    }
    return actors;
}

api_rooms.find_actors = function(actor_type, name, value)
{
    var actors = [];
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (actor.actor_type == actor_type && (name==null || actor.state[name] == value))
            actors[actors.length] = actor;
    }
    return actors;
}

api_rooms.docked_actors = function(actor_type)
{
    var docked = [];
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (api_rooms.player_actor && actor.parent_id == api_rooms.player_actor.actor_id && actor_type == actor.actor_type)
            docked[docked.length] = actor;
    }
    return docked;
}

