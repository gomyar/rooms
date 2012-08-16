
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
    'floor_tile': 'maps/floor_tile.png',
    'mansion_map': 'maps/mansion_map.png',

    'aunt': "/character_models/aunt.png",
    'dilettante': "/character_models/dilettante.png",
    'investigator': "/character_models/investigator.png",
    'major': "/character_models/major.png",
    'butler': "/character_models/butler.png",
    'gladys': "/character_models/gladys.png",
    'jezabel': "/character_models/jezabel.png",
    'professor': "/character_models/professor.png",

    'diningroom_table': 'room_objects/diningroom_table.png',
    'diningroom_chair': 'room_objects/diningroom_chair.png',
    'diningroom_chair_right': 'room_objects/diningroom_chair_right.png',
    'diningroom_chair_left': 'room_objects/diningroom_chair_left.png',
    'diningroom_chair_up': 'room_objects/diningroom_chair_up.png',
    'diningroom_chair_down': 'room_objects/diningroom_chair_down.png',
    'marble_side_table': 'room_objects/marble_side_table.png',
    'couch_east': 'room_objects/couch_east.png',
    'large_painting_west': 'room_objects/large_painting_west.png'
};

var background_img;

var loaded_script_file;
var loaded_chat_script_file;

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
            console.log("Error calling "+url+" : "+errorText);
        },
        'type': 'POST'
    });
}

function draw_previous_paths(ctx)
{
    ctx.strokeStyle = "rgb(0,0,100)";
    for (var p=0; p<previous_paths.length; p++)
    {
        var path = previous_paths[p];
        for (var i=0; i<path.length - 1; i++)
        {
            ctx.beginPath();
            ctx.moveTo(path[i][0], path[i][1]);
            ctx.lineTo(path[i+1][0], path[i+1][1]);
            ctx.stroke();
        }
    }
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
}

var angle = 0;

Sprite.prototype.set_model = function(model)
{
    this.model = model;
    this.img = images[this.model];
}

Sprite.prototype.is_walking = function()
{
    return get_now() < this.path[this.path.length-1][2] * 1000;
}

Sprite.prototype.drawPath = function(ctx)
{
    draw_previous_paths(ctx);
    ctx.strokeStyle = "rgb(0,0,200)";
    for (var i=0;i<this.path.length-1;i++)
    {
        ctx.beginPath();
        ctx.arc(this.path[i+1][0], this.path[i+1][1],10,0,Math.PI*2);
        ctx.closePath();
        ctx.stroke();

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

//    this.drawPath(ctx);

     ctx.save();
    ctx.translate(this.x(), this.y());

/*    ctx.strokeStyle = "rgb(0,0,0)";
    ctx.fillStyle = "rgb(0,0,0)";
    ctx.fillText("("+Math.round(this.x())+","+Math.round(this.y())+")",
        30, 0);*/

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
    if (this.id == player_id)
        service_call("/game/" + instance_uid + "/" + this.id + "/exposed_commands", {}, show_commands);
    else
        service_call("/game/" + instance_uid + "/" + this.id + "/exposed_methods", {}, show_commands);

}

Sprite.prototype.deselect = function()
{
    this.selected = false;
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
        command_item.attr("command", command.name);
        command_item.click(function() {
            $(".actor_commands").remove();
            command_lookup[$(this).attr('command')](); 
        });


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
    if (sprite)
    {
        console.log("found: "+sprite);
        select_sprite(sprite);
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
    service_call("/game/"+instance_uid+"/"+player_id+"/move_to",
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
    for (var i=0; i<room.map_objects.length; i++)
    {
        var map_object = room.map_objects[i];
        ctx.drawImage(map_object.img, map_object.position[0], map_object.position[1], map_object.width, map_object.height);
    }
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
    socket.send(instance_uid);
}

function onclose()
{
    console.log("Connection lost");
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
                }
                if (actor.actor_type == "NpcActor")
                {
                    var sprite = create_actor_sprite(actor);
                    sprites[actor.actor_id] = sprite;
                }

                else if (actor.actor_type == "Door")
                {
                    sprite = new Sprite(actor.actor_id);
                    sprite.draw = draw_door;
                    sprite.select = exit_through_door;
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
            console.log("Actor update for "+message.kwargs.actor_id);
            sprites[message.kwargs.actor_id].path = message.kwargs.path;
            sprites[message.kwargs.actor_id].optionalRedraw();
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
//            console.log("heartbeat");
        }
        else if (message.command == "disconnect")
        {
            console.log("Disconnected");
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
    if ($(".scripts").length > 0)
        $(".scripts").remove();
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

function load_script(script_file)
{
    loaded_script_file = script_file;
    service_call("/admin/load_script", { "script_file": script_file }, show_script_file);
}

function save_script(script_file, script_contents)
{
    service_call("/admin/save_script", { "script_file": script_file, "script_contents": script_contents }, script_saved);
}

function script_saved(data)
{
    $(".scriptedit").remove();
    if (data.success)
        alert("Script saved");
    else
        alert(data.stacktrace);
}

function show_script_file(data)
{
    var textarea = $("<textarea>", {'class': 'editor', 'text': data, 'id': 'editarea' });
    $(".scriptedit").remove();
    var scriptedit_div = $("<div>", { "class": "scriptedit" }).append(
        textarea 
    );
    $("#main").append(scriptedit_div);

    var myCodeMirror = CodeMirror.fromTextArea(textarea[0], {'name': 'text/x-python'});
    scriptedit_div.append(
        $("<div>", {'class': 'savebutton', 'text': 'Save' }).click(function(){
            save_script(loaded_script_file, myCodeMirror.getValue())}
        ),
        $("<div>", {'class': 'closebutton', 'text': 'Close' }).click(function() { $(".scriptedit").remove() })
    );
}

function load_chat_script(script_file)
{
    loaded_chat_cript_file = script_file;
    service_call("/admin/load_chat_script", { "script_file": script_file }, show_chat_script_file);
}

function show_chat_script_file(data)
{
    alert("Chat:"+data);
}

function show_scripts(data)
{
    if ($(".evidence").length > 0)
        $(".evidence").remove();
    if ($(".scripts").length > 0)
        $(".scripts").remove();
    else
    {
        var scripts_div = $("<div>", { "class": "scripts"});
        var actor_scripts_div = $("<div>", { "class": "actor_scripts"});
        for (i in data.scripts)
        {
            var script_file = data.scripts[i];
            var script_element = $("<div>", {'class': 'scripts_file', 'text': script_file});
            script_element.attr('script_file', script_file);
            script_element.click(function (){
                console.log("Loading "+script_file);
                load_script($(this).attr('script_file'));
            });

            actor_scripts_div.append(script_element);
        }
        actor_scripts_div.append($("<div>", {'class': 'buttonmenu'}).append(
            $("<div>", {'class': 'sbutton', 'text': 'Edit'}),
            $("<div>", {'class': 'sbutton', 'text': 'New'})
        ));
        var chats_div = $("<div>", { "class": "chat_scripts"});
        for (i in data.chat_scripts)
        {
            var script_file = data.chat_scripts[i];
            var script_element = $("<div>", {'class': 'scripts_file', 'text': script_file});
            script_element.attr('script_file', script_file);
            script_element.click(function (){
                console.log("Loading "+script_file);
                load_chat_script($(this).attr('script_file'));
            });

            chats_div.append(script_element);
        }
        chats_div.append($("<div>", {'class': 'buttonmenu'}).append(
            $("<div>", {'class': 'sbutton', 'text': 'Edit'}),
            $("<div>", {'class': 'sbutton', 'text': 'New'})
        ));

        scripts_div.append(actor_scripts_div);
        scripts_div.append(chats_div);
        $("#main").append(scripts_div);
    }
}

function menu_scripts_clicked(e)
{
    service_call("/admin/list_scripts",
        { }, show_scripts)
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
    $("#menu_scripts").click(menu_scripts_clicked);

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

