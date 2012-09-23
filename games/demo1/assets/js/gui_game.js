
var gui_game = {};

gui_game.sprites = {};
gui_game.selected_sprite = null;
gui_game.hovered_sprite = null;
gui_game.shown_commands = null;


gui_game.draw_door = function(ctx)
{
    ctx.strokeStyle = "rgb(255,255,255)";
    ctx.beginPath();
    ctx.arc(this.x(),this.y(),40,this.opens_direction-Math.PI/2,this.opens_direction + Math.PI/2);
    ctx.closePath();
    ctx.stroke();
}

gui_game.timeTo = function(start, end, speed)
{
    var x = end[0] - start[0];
    var y = end[1] - start[1];
    return Math.sqrt(x * x + y * y) / speed;
}

gui_game.exit_through_door = function()
{
    var door_id = this.id;
    gui_game.walk_to(this.x(), this.y());
    var timeTill = gui_game.timeTo([api_rooms.own_actor.x(), api_rooms.own_actor.y()],
        [this.x(), this.y()], api_rooms.own_actor.speed) * 1000.0;
    gui.walk_timeout = setTimeout(function() {
        api_rooms.exit_through_door(door_id);
    }, timeTill);
}

gui_game.canvas_clicked = function(e)
{
    var click_x = e.clientX - $("#screen").position().left - gui.viewport_x;
    var click_y = e.clientY - $("#screen").position().top - gui.viewport_y;
    console.log("clicked "+click_x+","+click_y);

    $(".actor_commands").remove();
    $("#chatOuter").remove();

    sprite = gui_game.findSprite(click_x, click_y);
    if (sprite)
    {
        console.log("found: "+sprite);
        gui_game.select_sprite(sprite);
    }
    else 
    {
        gui_game.walk_to(click_x, click_y)
    }
}

gui_game.select_sprite = function(sprite)
{
    if (gui_game.selected_sprite != null)
        gui_game.selected_sprite.deselect();
    gui_game.selected_sprite = sprite;
    gui_game.selected_sprite.select();
}

gui_game.walk_to = function(x, y)
{
    if (gui.walk_timeout)
        clearTimeout(gui.walk_timeout);
    api_rooms.walk_to(x, y);
}

gui_game.canvas_mousemove = function(e)
{
    var click_x = e.clientX - $("#screen").position().left - gui.viewport_x;
    var click_y = e.clientY - $("#screen").position().top - gui.viewport_y;

    var sprite = gui_game.findSprite(click_x, click_y);
    if (sprite)
    {
        sprite.hovered = true;
        gui_game.hovered_sprite = sprite;

        $(gui.canvas).css('cursor', 'pointer');
        gui.requestRedraw();
    }
    else
    {
        if (gui_game.hovered_sprite != null)
            gui_game.hovered_sprite.hovered = false;
        gui_game.hovered_sprite = null;
        $(gui.canvas).css('cursor', 'auto');
    }
}

gui_game.findSprite = function(x, y)
{
    for (var i in gui_game.sprites)
        if (gui_game.sprites[i].atPosition(x, y))
            return gui_game.sprites[i];
    return null;
}

gui_game.show_commands = function(commands)
{
    gui_game.shown_commands = commands;
    $(".actor_commands").remove();
    var command_div = $("<div>", { 'class': 'actor_commands' });
    command_div.css("left", gui_game.selected_sprite.x() + gui.viewport_x + 25);
    command_div.css("top", gui_game.selected_sprite.y() + gui.viewport_y - 25);

    for (var i in commands)
    {
        var command = commands[i];
        var command_item = $("<div>", { 'class': 'command_button', 'text': command.name } );
        command_item.attr("command", command.name);
        command_item.click(function() {
            $(".actor_commands").remove();
            api_rooms.command_lookup[$(this).attr('command')](); 
        });


        command_div.append(command_item);
    }
    $("#main").append(command_div);
}

gui_game.draw_room = function()
{
    for (object_id in api_rooms.room.map_objects)
    {
        var map_object = api_rooms.room.map_objects[object_id];
        gui.ctx.drawImage(map_object.img, map_object.position[0], map_object.position[1], map_object.width, map_object.height);
        gui.draw_text_centered(map_object.position[0], map_object.position[1],
            object_id)
    }
}

gui_game.create_actor_sprite = function(actor)
{
    sprite = new gui_sprite.Sprite(actor.actor_id);
    gui_game.sprites[actor.actor_id] = sprite;
    sprite.path = actor.path;
    sprite.speed = actor.speed;
    sprite.set_model(actor.model_type);
    return sprite;
}

gui_game.onmessage = function(msg)
{
    var messages = jQuery.parseJSON(msg.data);
    for (var i in messages)
    {
        var message = messages[i];
        if (message.command == "sync")
        {
            console.log("Sync: "+message.kwargs.actors.length+" actors");
            api_rooms.set_now(message.kwargs.now);
            actors = message.kwargs.actors;
            gui_game.sprites = {};
            for (var i=0; i<actors.length; i++)
            {
                var actor = actors[i];
                if (actor.actor_type == "PlayerActor")
                {
                    var sprite = gui_game.create_actor_sprite(actor);
                    gui_game.sprites[actor.actor_id] = sprite;
                    if (actor.actor_id == api_rooms.player_id)
                        api_rooms.own_actor = sprite;
                }
                if (actor.actor_type == "NpcActor")
                {
                    var sprite = gui_game.create_actor_sprite(actor);
                    gui_game.sprites[actor.actor_id] = sprite;
                }

                else if (actor.actor_type == "Door")
                {
                    sprite = new gui_sprite.Sprite(actor.actor_id);
                    sprite.draw = gui_game.draw_door;
                    sprite.select = gui_game.exit_through_door;
                    sprite.path = actor.path;
                    sprite.width = 80;
                    sprite.height = 80;
                    sprite.opens_direction = api_rooms.facing_directions[actor.opens_direction];
                    sprite.opens_dir= actor.opens_direction;
                    gui_game.sprites[actor.actor_id] = sprite;
                }
            }
            api_rooms.load_map('/room/'+api_rooms.instance_uid);
            $("#log").empty();
            for (var i in message.kwargs.player_log)
            {
                var text = message.kwargs.player_log[i].msg;
                var time = message.kwargs.player_log[i].time;
                gui_game.addLogEntry(text, time * 1000);
            }
            gui.requestRedraw();
        }
        else if (message.command == "actor_update")
        {
            gui_game.sprites[message.kwargs.actor_id].path = message.kwargs.path;
            gui_game.sprites[message.kwargs.actor_id].optionalRedraw();
        }
        else if (message.command == "player_joined_instance")
        {
            sprite = gui_game.create_actor_sprite(message.kwargs);
            sprite.optionalRedraw();

            if (message.kwargs.actor_id == api_rooms.player_id)
                api_rooms.own_actor = sprite;
        }
        else if (message.command == "actor_left_instance")
        {
            console.log("Actor left: "+message.kwargs.actor_id);
            delete gui_game.sprites[message.kwargs.actor_id];
            gui.requestRedraw();
        }
        else if (message.command == "actor_entered_room")
        {
            console.log("Actor entered: "+message.kwargs.actor_id);
            var sprite = gui_game.create_actor_sprite(message.kwargs);
            gui_game.sprites[message.kwargs.actor_id] = sprite;
            sprite.optionalRedraw();
        }
        else if (message.command == "actor_exited_room")
        {
            console.log("Actor exited: "+message.kwargs.actor_id);
            delete gui_game.sprites[message.kwargs.actor_id];
            gui.requestRedraw();
        }
        else if (message.command == "actor_heard")
        {
            console.log("Heard "+message.kwargs.msg);
            gui_game.sprites[message.kwargs.actor_id].speech_bubble(message.kwargs.msg);
        }
        else if (message.command == "log")
        {
            gui_game.addLogEntry(message.kwargs.msg);
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

gui_game.addLogEntry = function(message, time)
{
    var logtime = new Date(api_rooms.get_now()).toLocaleTimeString();
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

gui_game.initBackgroundImage = function()
{
    gui_assets.background_img = images['mansion_map'];
    gui.requestRedraw();
}

gui_game.menu_quit_clicked = function(e)
{
    api_rooms.leave_instance();
}

gui_game.show_evidence = function(data)
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

gui_game.menu_evidence_clicked = function(e)
{
    api_rooms.list_inventory(gui_game.show_evidence);
}


