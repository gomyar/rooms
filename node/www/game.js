
var server_time;
var local_time;
var instance_uid;
var player_id;

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
    console.log("Server time : "+new Date(server_time));
    console.log("Local time : "+new Date(local_time));
}

function distance(x1, y1, x2, y2)
{
    return Math.sqrt((x2-x1)^2, (y2-y1)^2);
}

var now = get_now();

function Sprite(id)
{
    this.id = id;
    this.path = [ [ 0.0, 0.0, get_now() ], [ 0.0, 0.0, get_now() ] ];
    this.start_time = get_now();
    this.end_time = get_now();
    this.start_x = 0;
    this.start_y = 0;
    this.end_x = 0;
    this.end_y = 0;
    this.width = 50;
    this.height = 50;
    this.selected = false;
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
    for (i=0;i<this.path.length-1;i++)
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

Sprite.prototype.set_position = function(x, y)
{
    this.start_x = x;
    this.start_y = y;
    this.end_x = x;
    this.end_y = y;
}

Sprite.prototype.set_vector = function(start_x, start_y, end_x, end_y,
    start_time, end_time)
{
    this.start_x = start_x;
    this.start_y = start_y;
    this.end_x = end_x;
    this.end_y = end_y;
    this.start_time = start_time;
    this.end_time = end_time;
}

Sprite.prototype.current_vector = function()
{
    now = get_now();
    if (now > this.path[this.path.length-1][2] * 1000)
        return [ this.path[this.path.length-2], this.path[this.path.length-1] ];
    index = 0;
    while (index < this.path.length - 2 && this.path[index + 1][2] * 1000 < now)
        index += 1;

    start_point = this.path[index];
    start_time = this.path[index][2] * 1000;
    end_point = this.path[index + 1];
    end_time = this.path[index + 1][2]* 1000;

    return [ start_point, end_point ];
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
    x2 = x1 + this.width / 2;
    y2 = y1 + this.height / 2;
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
var selected_sprite = null;
var viewport_x = 0;
var viewport_y = 0;

function findSprite(x, y)
{
    for (i in sprites)
        if (sprites[i].atPosition(click_x, click_y))
            return sprites[i];
    return null;
   
}

function clicked(e)
{
    click_x = e.clientX - $("#screen").position().left - viewport_x;
    click_y = e.clientY - $("#screen").position().top - viewport_y;
    console.log("clicked "+click_x+","+click_y);

    sprite = findSprite(click_x, click_y);
    if (sprite)
    {
        console.log("found: "+sprite);
        if (selected_sprite != null)
            selected_sprite.deselect();
        selected_sprite = sprite;
        selected_sprite.select();
        return;
    }
    else 
    {
        jQuery.post("/game/"+instance_uid+"/"+player_id+"/walk_to", { 
            x : click_x, y : click_y },
            function () { console.log("Ok"); });
    }

}

function draw()
{
    ctx.fillStyle = "rgb(0,0,0)";
    ctx.fillRect(0, 0, 500, 500);

    ctx.save()
    if (own_actor != null)
    {
        viewport_x = -(own_actor.x() - 250);
        viewport_y = -(own_actor.y() - 250);
        ctx.translate(viewport_x, viewport_y);
    }

    ctx.fillStyle = "rgb(0,100,0)";
    ctx.fillRect(0, 0, room.width, room.height);

    draw_map();

    for (i in sprites)
        sprites[i].draw(ctx);

    ctx.restore();

    setTimeout(draw, 10);
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
    for (i=0; i<map.length; i++)
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
//        parsed = jQuery.parseJSON(data);
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
    for (i in messages)
    {
        var message = messages[i];
        if (message.command == "sync")
        {
            console.log("Sync: "+message.kwargs.actors.length+" actors");
            set_now(message.kwargs.now);
            actors = message.kwargs.actors;
            sprites = {};
            for (i=0; i<actors.length; i++)
            {
                sprite = new Sprite(actors[i].player_id);
                sprite.path = actors[i].path;
                sprites[actors[i].player_id] = sprite;
                if (actors[i].player_id == player_id)
                    own_actor = sprite;
            }
            load_map(message.kwargs.map);
        }
        else if (message.command == "actor_update")
        {
            console.log("Actor update: "+message.kwargs.player_id);
            sprites[message.kwargs.player_id].path = message.kwargs.path;
        }
        else if (message.command == "actor_joined")
        {
            console.log("Actor joined: "+message.kwargs.player_id);
            sprite = new Sprite(message.kwargs.player_id);
            sprites[message.kwargs.player_id] = sprite;
            sprite.path = message.kwargs.path;

            if (message.kwargs.player_id == player_id)
                own_actor = sprite;
        }
        else if (message.command == "actor_left")
        {
            console.log("Actor left: "+message.kwargs.player_id);
            delete sprites[message.kwargs.player_id];
        }
        else if (message.command == "heartbeat")
        {
            console.log("heartbeat");
        }
    }
}

function init()
{
    console.log("init");
    $("#player_overlay").css("display", "none");

    canvas = $("#screen")[0];
    $("#screen").click(clicked);

    ctx = canvas.getContext("2d");

    socket = new WebSocket("ws://"+window.location.hostname+":8080/socket");
    socket.onmessage = onmessage;
    socket.onopen = onopen;

    console.log("Drawing");
    setTimeout(draw, 10);
}

// Thank you stackoverflow
function getParameter(paramName)
{
    var searchString = window.location.search.substring(1),
    i, val, params = searchString.split("&");

    for (i=0;i<params.length;i++)
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

