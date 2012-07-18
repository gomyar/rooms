
var server_time;
var local_time;
var instance_uid;
var player_id;

var redraw_until;
var walk_timeout = 0;

var previous_paths = [];

var facing_directions = {
    'north': Math.PI / 2,
    'south': Math.PI + Math.PI / 2,
    'east': Math.PI,
    'west': 0
};

var map_images = {
    'floor_tile_marble': 'images/floor_tile_marble.png',
    'investigator': 'images/walkingman.png',
    'orc': 'images/orc.png',
    'gold': 'images/gold_item.png'
};

var background_img;

function show_chat_window(message)
{
    $("#chatOuter").remove();
    if (message.command == "end_chat")
    {
        return;
    }
    console.log("Start chat with: "+message);
    var chatChoices = $("<div>", {'id': 'chatChoices'});
    for (i in message.choices)
    {
        var choice = message.choices[i];
        var choice_div = $("<div>", { "class": "chatChoice" });
        choice_div.text(choice);
        $(choice_div).attr('choice', choice);
        choice_div.click(function(e){
            service_call("/game/" + instance_uid + "/" + message.actor_id + "/chat", { "message": $(this).attr('choice') }, show_chat_window);
        });
        chatChoices.append(choice_div);
    }
    var chatDiv = $("<div>", {'id': 'chatOuter'}).append(
        $("<div>", {'id': 'chatText', 'text': message.msg}),
        chatChoices
    );
    chatDiv.css("left", $(window).width() / 2 - 175);
    $("#main").append(chatDiv);
}

function command_chat()
{
    service_call("/game/" + instance_uid + "/" + selected_sprite.id + "/chat", {}, show_chat_window);
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

function draw_door(ctx)
{
    ctx.strokeStyle = "rgb(255,255,255)";
    ctx.beginPath();
    ctx.arc(this.x(),this.y(),40,this.opens_direction-Math.PI/2,this.opens_direction + Math.PI/2);
    ctx.closePath();
    ctx.stroke();
}

function exited(data)
{
    console.log("Exited successfully");
}

function timeTo(start, end, speed)
{
    var x = end[0] - start[0];
    var y = end[1] - start[1];
    return Math.sqrt(x * x + y * y) / speed;
}

function exit_through_door()
{
    var door_id = this.id;
    walk_to(this.x(), this.y());
    var timeTill = timeTo([own_actor.x(), own_actor.y()],
        [this.x(), this.y()], own_actor.speed) * 1000.0;
    walk_timeout = setTimeout(function() {
        exit_door(door_id);
    }, timeTill);
}

function attack_orc()
{
    var orc_id = this.id;
    walk_to(this.x(), this.y());
    var timeTill = timeTo([own_actor.x(), own_actor.y()],
        [this.x(), this.y()], own_actor.speed) * 1000.0;
    walk_timeout = setTimeout(function() {
        perform_attack(orc_id);
    }, timeTill);
}

function perform_attack()
{
    service_call("/game/" + instance_uid + "/" + this.id + "/attack",
        { }, attacked)
}

function pickup_item()
{
    service_call("/game/" + instance_uid + "/" + this.id + "/pick_up",
        { }, function(){ console.log("Picked up");});
}

function attacked(data)
{
    console.log("Attacked");
}

function exit_door(door_id)
{
    service_call("/game/" + instance_uid + "/" + player_id + "/exit",
        { "door_id": door_id }, exited)
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
}

function canvas_clicked(e)
{
    var click_x = e.clientX - $("#screen").position().left - viewport_x;
    var click_y = e.clientY - $("#screen").position().top - viewport_y;
    console.log("clicked "+click_x+","+click_y);

    $(".actor_commands").remove();
    $("#chatOuter").remove();

    sprite = findSprite(click_x, click_y);
    if (sprite != null && sprite != own_actor)
    {
        sprite.clicked();
    }
    else 
    {
        walk_to(click_x, click_y)
    }
}

function walk_to(x, y)
{
    if (walk_timeout)
        clearTimeout(walk_timeout);
    service_call("/game/"+instance_uid+"/"+player_id+"/walk_to",
        { x : x, y : y },
        function () {  });
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
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (background_img != null)
        ctx.drawImage(background_img, viewport_x, viewport_y);

    ctx.save()
    if (own_actor != null)
    {
        viewport_x = -(own_actor.x() - canvas.width / 2);
        viewport_y = -(own_actor.y() - canvas.height / 2);
        ctx.translate(viewport_x, viewport_y);
    }


    draw_room();


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

var room = { width: 500, height: 500, position: [0, 0], map_objects: [] };

function draw_room()
{
    ctx.drawImage(images['floor_tile_marble'], room.position[0], room.position[1], room.width, room.height);
}

function load_map(map_url)
{
    jQuery.get(map_url, function(data) {
        room = jQuery.parseJSON(data);
        for (i in room.map_objects)
        {
            var map_object = room.map_objects[i];
            map_object.img = images[map_object.object_type];
        }
    });
}

var actors = [];
var own_actor;
var socket;

function onopen()
{
    console.log("Connected");
    socket.send(player_id);
    console.log("Sending instance uid:"+instance_uid);
    socket.send(instance_uid);
}

function onclose()
{
//    alert("Connection lost");
    console.log("connection lost");
//    window.location = "http://localhost:8000";
}

function create_actor_sprite(actor)
{
    sprite = new Sprite(actor.actor_id);
    sprites[actor.actor_id] = sprite;
    sprite.path = actor.path;
    sprite.speed = actor.speed;
    sprite.set_model(actor.model_type);
    return sprite;
}

function onmessage(msg)
{
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
                var actor = actors[i];
                if (actor.actor_type == "PlayerActor")
                {
                    var sprite = create_actor_sprite(actor);
                    previous_paths[previous_paths.length] = sprite.path;
                    sprites[actor.actor_id] = sprite;
                    if (actor.actor_id == player_id)
                        own_actor = sprite;
                    sprite.action = actor.action;
                }
                if (actor.actor_type == "NpcActor")
                {
                    var sprite = create_actor_sprite(actor);
                    sprite.clicked = perform_attack;
                    sprites[actor.actor_id] = sprite;
                    sprite.action = actor.action;
                }
                if (actor.actor_type == "ItemActor")
                {
                    var sprite = create_actor_sprite(actor);
                    sprite.clicked = pickup_item;
                    sprites[actor.actor_id] = sprite;
                    sprite.action = actor.action;
                }
                else if (actor.actor_type == "Door")
                {
                    sprite = new Sprite(actor.actor_id);
                    sprite.draw = draw_door;
                    sprite.clicked = exit_through_door;
                    sprite.path = actor.path;
                    sprite.width = 80;
                    sprite.height = 80;
                    sprite.opens_direction = facing_directions[actor.opens_direction];
                    sprite.opens_dir= actor.opens_direction;
                    sprites[actor.actor_id] = sprite;
                }
            }
            load_map('/room/'+instance_uid);
            $("#log").empty();
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
//            console.log("Actor update: "+message.kwargs.actor_id);
            previous_paths[previous_paths.length] = sprites[message.kwargs.actor_id].path;
            sprites[message.kwargs.actor_id].path = message.kwargs.path;
            sprites[message.kwargs.actor_id].optionalRedraw();
            sprites[message.kwargs.actor_id].action = message.kwargs.action;
            console.log("action="+message.kwargs.action.action_id);
        }
        else if (message.command == "player_joined_instance")
        {
            console.log("Actor joined: "+message.kwargs.actor_id);
            sprite = create_actor_sprite(message.kwargs);
            sprite.optionalRedraw();

            if (message.kwargs.actor_id == player_id)
                own_actor = sprite;
        }
        else if (message.command == "actor_left_instance")
        {
            console.log("Actor left: "+message.kwargs.actor_id);
            delete sprites[message.kwargs.actor_id];
            requestRedraw();
        }
        else if (message.command == "actor_entered_room")
        {
            console.log("Actor entered: "+message.kwargs.actor_id);
            var sprite = create_actor_sprite(message.kwargs);
            sprites[message.kwargs.actor_id] = sprite;
            sprite.optionalRedraw();
        }
        else if (message.command == "actor_exited_room")
        {
            console.log("Actor exited: "+message.kwargs.actor_id);
            delete sprites[message.kwargs.actor_id];
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
        else if (message.command == "disconnect")
        {
            alert("Disconnected");
        }
    }
}

function addLogEntry(message, time)
{
    var logtime = new Date(get_now()).toLocaleTimeString();
    if (time != null)
        logtime = new Date(time).toLocaleTimeString();
    $("#log").append(
        $("<div>", { 'class': 'logEntry' }).append(
            $("<div>", { 'class': 'logTime', 'text': logtime }),
            $("<div>", { 'class': 'logText', 'text': message })
        )
    );
    $("#log").scrollTop($("#log").attr("scrollHeight"));
}

function initBackgroundImage()
{
    background_img = images['mansion_map'];
    requestRedraw();
}

function menu_quit_clicked(e)
{
    service_call("/game/" + instance_uid + "/" + player_id + "/leave_instance",
        { }, function () { console.log("Leave sent"); })
}

function show_evidence(data)
{
    if ($(".evidence").length > 0)
        $(".evidence").remove();
    else
    {
        var evidence_div = $("<div>", { "class": "evidence"});
        for (npc_id in data)
        {
            var npc_notes = data[npc_id];
            evidence_div.append($("<div>", {'class': 'evidence_item'}).append(
                $("<div>", {'class': 'profile '+npc_notes.npc_id}),
                $("<div>", {'class': 'category '+npc_notes.category, 'text': npc_notes.category}),
                $("<div>", {'class': 'description', 'text': npc_notes.description})
            ));
        }
        $("#main").append(evidence_div);
    }
}

function menu_evidence_clicked(e)
{
    service_call("/game/" + instance_uid + "/" + player_id + "/list_inventory",
        { }, show_evidence)
}

function init()
{
    console.log("init");
    $("#player_overlay").css("display", "none");

    canvas = $("#screen")[0];
    $(canvas).click(canvas_clicked);
    $(canvas).mousemove(canvas_mousemove);

    $("#menu_quit").click(menu_quit_clicked);
    $("#menu_evidence").click(menu_evidence_clicked);

    $(window).resize(function() { resetCanvas(); draw(); });

    resetCanvas();

    socket = new WebSocket("ws://"+window.location.hostname+":8080/socket");
    socket.onmessage = onmessage;
    socket.onopen = onopen;
    socket.onclose = onclose;
    socket.onerror = onclose;

    loadImages(map_images, function() {
        initBackgroundImage();
    });
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

