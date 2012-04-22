
var server_time;
var local_time;
var instance_uid;
var player_id;

var redraw_until;

function command_chat()
{
    service_call("/game/" + instance_uid + "/" + selected_sprite.id + "/chat", {}, function () { console.log("Unneeded callback"); });
}

function command_sleep_in()
{
}

function command_walk_to()
{
}

function command_get_out()
{
}

var command_lookup = {
    "chat": command_chat,
    "sleep_in": command_sleep_in,
    "walk_to": command_walk_to,
    "get_out": command_get_out
};

function get_now()
{
    local_now = new Date().getTime();
    ticks = local_now - local_time;
    return ticks + server_time;
}

function set_now(now_time)
{
    server_time = now_time * 1000;
    local_time = new Date().getTime();
    redraw_until = get_now();
    console.log("Server time : "+new Date(server_time));
    console.log("Local time : "+new Date(local_time));
}

function distance(x1, y1, x2, y2)
{
    return Math.sqrt((x2-x1)^2, (y2-y1)^2);
}

function service_call(url, data, callback)
{
    $.ajax({
        'url': url,
        'data': data,
        'success': function(data) {
            callback(jQuery.parseJSON(data));
        },
        'error': function(jqXHR, errorText) {
            alert("Error calling "+url+" : "+errorText);
        },
        'type': 'POST'
    });
}

var now = get_now();

function Sprite(id)
{
    this.id = id;
    this.path = [ [ 0.0, 0.0, get_now() ], [ 0.0, 0.0, get_now() ] ];
    this.width = 50;
    this.height = 50;
    this.selected = false;
    this.hovered = false;
    this.img = new Image();
    this.img.src = "/walkingman.png";
}

var angle = 0;

Sprite.prototype.is_walking = function()
{
    return get_now() < this.path[this.path.length-1][2] * 1000;
}

Sprite.prototype.draw = function(ctx)
{
    if (this.hovered == true)
        draw_rect(this.x()-2-this.width/2, this.y()-2-this.height/2,
            this.width + 4, this.height + 4, "rgb(200,200,0)");
    if (this.selected == true)
        draw_rect(this.x()-2-this.width/2, this.y()-2-this.height/2,
            this.width + 4, this.height + 4, "rgb(0,200,0)");

    vector = this.current_vector();

    angle = Math.atan2(vector[1][1] - vector[0][1],
        vector[1][0] - vector[0][0]);

    if (this.is_walking())
        offset = Math.round((new Date().getTime() % 1400) / 200);
    else
        offset = 0;

    ctx.strokeStyle = "rgb(0,0,200)";
    for (var i=0;i<this.path.length-1;i++)
    {
        ctx.beginPath();
        ctx.moveTo(this.path[i][0], this.path[i][1]);
        ctx.lineTo(this.path[i+1][0], this.path[i+1][1]);
        ctx.stroke();
    }
    ctx.strokeStyle = "rgb(200,200,200)";
    ctx.beginPath();
    ctx.moveTo(vector[0][0], vector[0][1]);
    ctx.lineTo(vector[1][0], vector[1][1]);
    ctx.stroke();

    ctx.save();
    ctx.translate(this.x(), this.y());

    ctx.strokeStyle = "rgb(0,0,0)";
    ctx.fillStyle = "rgb(0,0,0)";
    ctx.fillText("("+Math.round(this.x())+","+Math.round(this.y())+")",
        30, 0);

    ctx.rotate(angle);
    ctx.translate(- this.width / 2, - this.height / 2);
    ctx.drawImage(this.img, 0, offset * 50, 50, 50, 0, 0, 50, 50);
    ctx.restore();
}

Sprite.prototype.current_vector = function()
{
    now = get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
        return [ this.path[this.path.length-2], this.path[this.path.length-1] ];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    var start_point = this.path[index];
    var end_point = this.path[index + 1];

    return [ start_point, end_point ];
}

Sprite.prototype.end_time = function()
{
    return this.path[this.path.length-1][2] * 1000;
}

Sprite.prototype.x = function()
{
    now = get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
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

    now = get_now();
    if (now > end_time)
        return end_x;
    diff_x = end_x - start_x;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_x;
    inc = (now - start_time) / diff_t;
    return start_x + diff_x * inc;
}

Sprite.prototype.y = function()
{
    now = get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
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

    now = get_now();
    if (now > end_time)
        return end_y;
    diff_y = end_y - start_y;
    diff_t = end_time - start_time;
    if (diff_t <= 0)
        return end_y;
    inc = (now - start_time) / diff_t;
    return start_y + diff_y * inc;
}

Sprite.prototype.walk_to = function(x, y, end_time)
{
    console.log("sprite: "+this.id+" walking to "+x+","+y);
    this.start_x = this.x();
    this.start_y = this.y();
    this.end_x = x;
    this.end_y = y;
    this.start_time = get_now();
    if (end_time != null)
        this.end_time = end_time;
    else
        this.end_time = this.start_time + 2000;
    this.optionalRedraw();
}

Sprite.prototype.optionalRedraw = function()
{
    if (redraw_until <= this.end_time())
    {
        redraw_until = this.end_time();
        requestRedraw();
    }
}

Sprite.prototype.time_till = function(start_x, start_y, end_x, end_y)
{
    x = start_x;
    y = start_y;
    console.log("till: "+x+","+y+" "+end_x+","+end_y);
    dist = distance(x, y, end_x, end_y);
    console.log("dist:"+dist);
    return dist / 1000;
}

Sprite.prototype.atPosition = function(x, y)
{
    x1 = this.x() - this.width / 2;
    y1 = this.y() - this.height / 2;
    x2 = x1 + this.width;
    y2 = y1 + this.height;
    return x > x1 && x < x2 && y > y1 && y < y2;
}

Sprite.prototype.select = function()
{
    this.selected = true;
}

Sprite.prototype.deselect = function()
{
    this.selected = false;
}

var canvas;
var ctx;
var sprites = {};
var selected_sprite;
var hovered_sprite;
var viewport_x = 0;
var viewport_y = 0;
var shown_commands;

function resetCanvas()
{
    canvas.width = $("#main").width();
    canvas.height = $("#main").height();
    ctx=canvas.getContext("2d");
}

function findSprite(x, y)
{
    for (var i in sprites)
        if (sprites[i].atPosition(x, y))
            return sprites[i];
    return null;
}

function show_commands(commands)
{
    shown_commands = commands;
    $(".actor_commands").remove();
    var command_div = $("<div>", { 'class': 'actor_commands' });
    command_div.css("left", selected_sprite.x() + viewport_x + 25);
    command_div.css("top", selected_sprite.y() + viewport_y - 25);

    for (var i in commands)
    {
        var command = commands[i];
        var command_item = $("<div>", { 'class': 'command_button', 'text': command.name } );
        command_item.click(function() { $(".actor_commands").remove(); command_lookup[command.name](); });
        command_div.append(command_item);
    }
    $("#main").append(command_div);
}

function select_sprite(sprite)
{
    if (selected_sprite != null)
        selected_sprite.deselect();
    selected_sprite = sprite;
    selected_sprite.select();
    if (sprite.id == player_id)
        service_call("/game/" + instance_uid + "/" + sprite.id + "/exposed_commands", {}, show_commands);
    else
        service_call("/game/" + instance_uid + "/" + sprite.id + "/exposed_methods", {}, show_commands);
}

function canvas_clicked(e)
{
    var click_x = e.clientX - $("#screen").position().left - viewport_x;
    var click_y = e.clientY - $("#screen").position().top - viewport_y;
    console.log("clicked "+click_x+","+click_y);

    $(".actor_commands").remove();

    sprite = findSprite(click_x, click_y);
    if (sprite)
    {
        console.log("found: "+sprite);
        select_sprite(sprite);
    }
    else 
    {
        service_call("/game/"+instance_uid+"/"+player_id+"/walk_to",
            { x : click_x, y : click_y },
            function () { console.log("Ok"); });
    }
}

function canvas_mousemove(e)
{
    var click_x = e.clientX - $("#screen").position().left - viewport_x;
    var click_y = e.clientY - $("#screen").position().top - viewport_y;

    var sprite = findSprite(click_x, click_y);
    if (sprite)
    {
        sprite.hovered = true;
        hovered_sprite = sprite;

        $(canvas).css('cursor', 'pointer');
        requestRedraw();
    }
    else
    {
        if (hovered_sprite != null)
            hovered_sprite.hovered = false;
        hovered_sprite = null;
        $(canvas).css('cursor', 'auto');
    }
}

function draw()
{
    ctx.fillStyle = "rgb(0,0,0)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.save()
    if (own_actor != null)
    {
        viewport_x = -(own_actor.x() - canvas.width / 2);
        viewport_y = -(own_actor.y() - canvas.height / 2);
        ctx.translate(viewport_x, viewport_y);
    }

    ctx.fillStyle = "rgb(0,100,0)";
    ctx.fillRect(0, 0, room.width, room.height);

    draw_map();

    for (var i in sprites)
        sprites[i].draw(ctx);

    ctx.restore();

    if (get_now() < redraw_until)
        requestRedraw();
}

function requestRedraw()
{
    setTimeout(draw, 20);
}

function draw_rect(x, y, width, height, color)
{
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.rect(x, y, width, height);
    ctx.closePath();
    ctx.stroke();
}

function fill_rect(x, y, width, height, color)
{
    ctx.fillStyle = color;
    ctx.fillRect(x, y, width, height);
}

var map = [];
var room = { width: 500, height: 500 };

function draw_map()
{
    for (var i=0; i<map.length; i++)
    {
        tile = map[i];
        if (tile.type == "rect")
            fill_rect(tile.x, tile.y, tile.width,
                tile.height, "rgb(100,100,140)");
        if (tile.type == "poly")
        {
            ctx.fillStyle = "rgb(100,100,140)";
            ctx.beginPath();
            ctx.moveTo(tile.vertices[0][0], tile.vertices[0][1]);
            for (v=1; v<tile.vertices.length; v++)
                ctx.lineTo(tile.vertices[v][0], tile.vertices[v][1]);
            ctx.closePath();
            ctx.fill();
        }
    }
}

function load_map(map_url)
{
    jQuery.get(map_url, function(data) {
        console.log("Loaded map: "+data);
        parsed = data;

        map = parsed.rooms.pitch.objects;
        room = parsed.rooms.pitch;
        console.log("Parsed map: "+parsed);
    });
}

var actors = [];
var own_actor;
var socket;

function onopen()
{
    console.log("Connected");
    socket.send(player_id);
    socket.send(instance_uid);
}

function onmessage(msg)
{
    console.log("Got: "+msg.data);
    var messages = jQuery.parseJSON(msg.data);
    for (var i in messages)
    {
        var message = messages[i];
        if (message.command == "sync")
        {
            console.log("Sync: "+message.kwargs.actors.length+" actors");
            set_now(message.kwargs.now);
            actors = message.kwargs.actors;
            sprites = {};
            for (var i=0; i<actors.length; i++)
            {
                sprite = new Sprite(actors[i].actor_id);
                sprite.path = actors[i].path;
                sprites[actors[i].actor_id] = sprite;
                if (actors[i].actor_id == player_id)
                    own_actor = sprite;
            }
            load_map(message.kwargs.map);
            for (var i in message.kwargs.player_log)
            {
                var text = message.kwargs.player_log[i].msg;
                var time = message.kwargs.player_log[i].time;
                addLogEntry(text, time * 1000);
            }
            requestRedraw();
        }
        else if (message.command == "actor_update")
        {
            console.log("Actor update: "+message.kwargs.actor_id);
            sprites[message.kwargs.actor_id].path = message.kwargs.path;
            sprites[message.kwargs.actor_id].optionalRedraw();
        }
        else if (message.command == "actor_joined")
        {
            console.log("Actor joined: "+message.kwargs.player_id);
            sprite = new Sprite(message.kwargs.player_id);
            sprites[message.kwargs.player_id] = sprite;
            sprite.path = message.kwargs.path;
            sprite.optionalRedraw();

            if (message.kwargs.player_id == player_id)
                own_actor = sprite;
        }
        else if (message.command == "actor_left")
        {
            console.log("Actor left: "+message.kwargs.player_id);
            delete sprites[message.kwargs.player_id];
            requestRedraw();
        }
        else if (message.command == "log")
        {
            addLogEntry(message.kwargs.msg);
        }
        else if (message.command == "heartbeat")
        {
            console.log("heartbeat");
        }
    }
}

function addLogEntry(message, time)
{
    var logtime = new Date(get_now()).toLocaleTimeString();
    if (time != null)
        logtime = new Date(time).toLocaleTimeString();
    $("#log").prepend(
        $("<div>", { 'class': 'logEntry' }).append(
            $("<div>", { 'class': 'logTime', 'text': logtime }),
            $("<div>", { 'class': 'logText', 'text': message })
        )
    );
}

function init()
{
    console.log("init");
    $("#player_overlay").css("display", "none");

    canvas = $("#screen")[0];
    $(canvas).click(canvas_clicked);
    $(canvas).mousemove(canvas_mousemove);

    $(window).resize(function() { resetCanvas(); draw(); });

    resetCanvas();

    socket = new WebSocket("ws://"+window.location.hostname+":8080/socket");
    socket.onmessage = onmessage;
    socket.onopen = onopen;

    console.log("Drawing");
    requestRedraw();
}

// Thank you stackoverflow
function getParameter(paramName)
{
    var searchString = window.location.search.substring(1),
    i, val, params = searchString.split("&");

    for (var i=0;i<params.length;i++)
    {
        val = params[i].split("=");
        if (val[0] == paramName)
        {
        return unescape(val[1]);
        }
    }
    return null;
}

function init_signin()
{
    console.log("init signin");
    player_id = getParameter("player_id");
    instance_uid = getParameter("instance_uid");
    init();
}

$(document).ready(init_signin);

