
var gui = {};

gui.canvas = null;
gui.ctx = null;

// Redraw timeout
gui.redraw_until = 0;
gui.walk_timeout = 0;
gui.redraw_timeout = null;

// Viewport
gui.viewport_x = 0;
gui.viewport_y = 0;
gui.zoom = 1.0;

// Input
gui.shown_commands = null;
gui.mouse_down = false;
gui.move_start_x = 0;
gui.move_start_y = 0;
gui.swallow_click = false;

gui.selected_actor = null;
gui.highlighted_actor = null;

gui.draw_invisible_actors = false;


gui.init = function(canvas)
{
    console.log("GUI Init");
    gui.canvas = canvas;

    $(gui.canvas).click(gui.canvas_clicked);
    $(gui.canvas).mousemove(gui.canvas_mousemove);
    $(gui.canvas).mousedown(gui.canvas_mousedown);
    $(gui.canvas).mouseup(gui.canvas_mouseup);
    $(gui.canvas).mouseover(gui.canvas_mouseover);
    $(gui.canvas).mouseout(gui.canvas_mouseout);
    $(gui.canvas).mousewheel(gui.canvas_mousewheel);

    $(window).resize(function() { gui.resetCanvas();  });
    gui.resetCanvas();
}


gui.center_on_room = function() {
    var x1 = null;
    var y1 = null;
    var x2 = null;
    var y2 = null;

    var room = api_rooms.room;
    x1 = room.position.x - room.width / 2;
    y1 = room.position.y - room.height / 2;
    x2 = room.position.x + room.width / 2;
    y2 = room.position.y + room.width / 2;

    gui.viewport_x = (x1 + x2) / 2;
    gui.viewport_y = (y1 + y2) / 2;
    gui.zoom = 1.2 * (y2 - y1) / gui.canvas.height;
    gui.requestRedraw();
}


gui.canvas_mousemove = function(e)
{
    gui.mouse_client_x = (e.clientX - $(gui.canvas).offset().left);
    gui.mouse_client_y = (e.clientY - $(gui.canvas).offset().top);

    if (gui.mouse_down)
    {
        var moved_x = gui.move_start_x - (e.clientX - $(gui.canvas).offset().left)
        var moved_y = gui.move_start_y - (e.clientY - $(gui.canvas).offset().top);
        gui.viewport_x += moved_x * gui.zoom;
        gui.viewport_y += moved_y * gui.zoom;
        gui.move_start_x = (e.clientX - $(gui.canvas).offset().left);
        gui.move_start_y = (e.clientY - $(gui.canvas).offset().top);

        if (Math.abs(moved_x) > 1 || Math.abs(moved_y) > 1)
            gui.swallow_click = true;

        gui.requestRedraw();
    }
    else
    {
        var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
        var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));

        var actors = gui.find_all_actors_at(click_x, click_y);
        if (actors.length > 0)
        {
            $(gui.canvas).css('cursor', 'pointer');
            if (!actors[0].docked_with && actors[0].visible)
                gui.highlighted_actor = actors[0];
            gui.requestRedraw();
        }
        else
        {
            $(gui.canvas).css('cursor', 'auto');
            gui.highlighted_actor = null;
            $('.actor_list').remove();
            gui.requestRedraw();
        }
    }
}

gui.show_actor_list = function(actors)
{
    // show list of selected actors
    admin.actor_list = actors;
    turtlegui.reload();
}


gui.canvas_mousedown = function(e)
{
    gui.mouse_down = true;
    gui.move_start_x = (e.clientX - $(gui.canvas).offset().left);
    gui.move_start_y = (e.clientY - $(gui.canvas).offset().top);

    if ($(".mapcontrol").size() > 0)
        gui.swallow_click = true;
}

gui.canvas_mouseup = function(e)
{
    gui.mouse_down = false;
}

gui.canvas_mousewheel = function(e, delta, deltaX, deltaY)
{
    var start_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
    var start_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));
    gui.zoom += gui.zoom * 0.1 * -deltaY;

    var end_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
    var end_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));
    var moved_x = start_x - end_x;
    var moved_y = start_y - end_y;
    gui.viewport_x += moved_x;
    gui.viewport_y += moved_y;

    gui.requestRedraw();
}

gui.canvas_clicked = function(e)
{
    $(".actor_list").remove();
    if (!gui.swallow_click)
    {
        var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
        var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));

        var actors = gui.find_all_actors_at(click_x, click_y);
        console.log("found");
        console.log(actors);
        if (actors.length > 1)
        {
            gui.show_actor_list(actors);
            gui.requestRedraw();
        }
        else if (actors.length == 1)
        {
            console.log("Single");
            gui.clear_actor_list();
            admin.select_actor(actors[0]);
        }
        turtlegui.reload();
    }
    console.log("clicked");
    gui.swallow_click = false;
}


gui.canvas_mouseover = function(e)
{
}

gui.canvas_mouseout = function(e)
{
    gui.mouse_down = false;
}


gui.find_actor = function(x, y)
{
    var actors = [];
    for (var i in api_rooms.actors)
        if (gui.at_position(api_rooms.actors[i], x, y))
            return api_rooms.actors[i];
    return null;
}

gui.should_draw_actor = function(actor)
{
    return true;
//    return !gui.draw_invisible_actors && (actor.docked_with || !actor.visible);
}

gui.at_position = function(actor, x, y)
{
    x1 = api_rooms.room.position.x + actor.x() - 12 * gui.zoom;
    y1 = api_rooms.room.position.y + actor.y() - 12 * gui.zoom;
    x2 = x1 + 25 * gui.zoom;
    y2 = y1 + 25 * gui.zoom;
    return x > x1 && x < x2 && y > y1 && y < y2;
}


gui.get_selected_actor = function()
{
    return admin.selected_actor;
}


gui.walk_to = function(x, y)
{
    if (gui.walk_timeout)
        clearTimeout(gui.walk_timeout);
    api_rooms.call_command("move_to", { x : x, y : y });
}

gui.find_all_actors_at = function(x, y)
{
    var actors = [];
    for (var i in api_rooms.actors)
        if (gui.at_position(api_rooms.actors[i], x, y))
            actors[actors.length] = api_rooms.actors[i];
    return actors;
}


gui.show_actor_list = function(actors)
{
    admin.actor_list = actors;
    turtlegui.reload();
}


gui.clear_actor_list = function()
{
    admin.actor_list = [];
    turtlegui.reload();
}

// ----------------- ols gui.js

gui.resetCanvas = function()
{
    gui.canvas.width = $("#screen").parent().width();
    gui.canvas.height = $("#screen").parent().height();
    gui.ctx=gui.canvas.getContext("2d");
    gui.requestRedraw();
}

gui.move_to_own_actor = function()
{
    if (api_rooms.player_actor != null)
    {
        gui.viewport_x = -(api_rooms.player_actor.x() - gui.canvas.width / 2);
        gui.viewport_y = -(api_rooms.player_actor.y() - gui.canvas.height / 2);
    }
}

gui.canvas_top = function()
{
    return gui.viewport_y - gui.zoom * gui.canvas.height / 2;
}

gui.canvas_left = function()
{
    return gui.viewport_x - gui.zoom * gui.canvas.width / 2;
}

gui.canvas_bottom = function()
{
    return gui.canvas_top() + gui.canvas.height * gui.zoom;
}

gui.canvas_right = function()
{
    return gui.canvas_left() + gui.canvas.width * gui.zoom;
}

gui.canvas_width = function()
{
    return gui.canvas_right() - gui.canvas_left();
}

gui.canvas_height = function()
{
    return gui.canvas_bottom() - gui.canvas_top();
}

gui.canvas_x = function(real_x)
{
    return gui.canvas.width * (real_x - gui.canvas_left()) / gui.canvas_width();
}

gui.canvas_y = function(real_y)
{
    return gui.canvas.height * (real_y - gui.canvas_top()) / gui.canvas_height();
}

gui.real_x = function(canvas_x)
{
    return gui.canvas_left() + canvas_x * gui.zoom;
}

gui.real_y = function(canvas_y)
{
    return gui.canvas_top() + canvas_y * gui.zoom;
}

gui.draw = function()
{
    gui.redraw_timeout = null;
    gui.ctx.fillStyle = "rgb(0,0,0)";
    gui.ctx.clearRect(0, 0, gui.canvas.width, gui.canvas.height);

    // Draw other rooms in map
    for (var room_id in admin.mapdata.rooms)
    {
        var room = admin.mapdata.rooms[room_id];
        gui.ctx.strokeStyle = "rgb(80, 80, 80)";

        var x1 = room.position.x - room.width / 2;
        var y1 = room.position.y - room.height / 2;

        gui.ctx.strokeRect(gui.canvas_x(x1), gui.canvas_y(y1), room.width / gui.zoom, room.height / gui.zoom)
    }

    // Draw current room
    gui.ctx.strokeStyle = "rgb(255, 255, 255)";
    var x1 = api_rooms.room.position.x - api_rooms.room.width / 2;
    var y1 = api_rooms.room.position.y - api_rooms.room.height / 2;

    gui.ctx.strokeRect(gui.canvas_x(x1), gui.canvas_y(y1), api_rooms.room.width / gui.zoom, api_rooms.room.height / gui.zoom)

    // Draw doors
    for (var door_index in api_rooms.room.doors)
    {
        var door = api_rooms.room.doors[door_index];

        gui.ctx.strokeStyle = "rgb(55, 55, 255)";
        gui.ctx.beginPath();
        gui.ctx.arc(gui.canvas_x(api_rooms.room.position.x + door.position.x), gui.canvas_y(api_rooms.room.position.y + door.position.y), 10, 0, Math.PI*2);
        gui.ctx.closePath();
        gui.ctx.stroke();
    }

    // Draw room objects
    for (object_id in api_rooms.room.room_objects)
    {
        var map_object = api_rooms.room.room_objects[object_id];
        var x1 = api_rooms.room.position.x + map_object.position.x - map_object.width / 2;
        var y1 = api_rooms.room.position.y + map_object.position.y - map_object.height / 2;

        gui.ctx.globalAlpha = 0.1;
        gui.fill_rect(
            gui.canvas_x(x1),
            gui.canvas_y(y1),
            map_object.width / gui.zoom,
            map_object.height / gui.zoom,
            "rgb(150, 200, 50)"
        );
        gui.ctx.globalAlpha = 1.0;
        gui.draw_rect(
            gui.canvas_x(x1),
            gui.canvas_y(y1),
            map_object.width / gui.zoom,
            map_object.height / gui.zoom,
            "rgb(150, 200, 50)"
        );
        gui.draw_text_centered(gui.canvas_x(api_rooms.room.position.x + map_object.position.x), gui.canvas_y(api_rooms.room.position.y + map_object.position.y), map_object.object_type, "rgb(150, 200, 50)");
    }

    // Draw actor paths
    for (var actor_id in api_rooms.actors)
    {
        gui.ctx.strokeStyle = "rgb(0,0,150)";
        var actor = api_rooms.actors[actor_id];
        gui.ctx.beginPath();
        gui.ctx.moveTo(gui.canvas_x(api_rooms.room.position.x + actor.vector.start_pos.x), gui.canvas_y(api_rooms.room.position.x + actor.vector.start_pos.y));
        gui.ctx.lineTo(gui.canvas_x(api_rooms.room.position.x + actor.vector.end_pos.x), gui.canvas_y(api_rooms.room.position.x + actor.vector.end_pos.y));
        gui.ctx.stroke();
    }
 
    // Draw actors
    for (var actor_id in api_rooms.actors)
    {
        var actor = api_rooms.actors[actor_id];
        if (!gui.should_draw_actor(actor))
            continue;
        gui.ctx.save();
        var ax = gui.canvas_x(api_rooms.room.position.x + actor.x());
        var ay = gui.canvas_y(api_rooms.room.position.y + actor.y());
        var docked_with_id = actor.docked_with;
        while (docked_with_id && api_rooms.actors[docked_with_id])
        {
            docked_with_id = api_rooms.actors[docked_with_id].docked_with;
            ay += 10;
        }
        gui.ctx.translate(ax, ay);
        gui.draw_actor(actor);
        gui.ctx.restore();

        //gui.draw_path(gui.ctx, actor.path);
    }
    if (gui.highlighted_actor)
        gui.draw_rect(gui.canvas_x(api_rooms.room.position.x + gui.highlighted_actor.x()) - 15, gui.canvas_y(api_rooms.room.position.y + gui.highlighted_actor.y()) - 15, 32, 32, "rgb(150,150,250)");
    if (gui.get_selected_actor())
        gui.draw_rect(gui.canvas_x(api_rooms.room.position.x + gui.get_selected_actor().x()) - 15, gui.canvas_y(api_rooms.room.position.y + gui.get_selected_actor().y()) - 15, 32, 32, "rgb(150,250,150)");

    gui.draw_text_centered(50, 20, "Viewport: ("+parseInt(gui.viewport_x)+", "+parseInt(gui.viewport_y)+")", "white");
    gui.draw_text_centered(50, 60, "Mouse: ("+parseInt(gui.mouse_client_x)+", "+parseInt(gui.mouse_client_y)+")", "white");
    gui.draw_text_centered(50, 80, "Zoom:" + Math.round(gui.zoom*100)/100, "white");


    var nowish = api_rooms.get_now();
    if (nowish < gui.redraw_until)
        gui.requestRedraw();
}


// ------ actor draw functions
gui.draw_path = function(ctx, path)
{
    ctx.strokeStyle = "rgb(0,0,200)";
    for (var i=0;i<path.length-1;i++)
    {
        ctx.beginPath();
        ctx.arc(gui.canvas_x(api_rooms.room.position.x + path[i+1][0]), gui.canvas_y(api_rooms.room.position.y + path[i+1][1]),10,0,Math.PI*2);
        ctx.closePath();
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(gui.canvas_x(api_rooms.room.position.x + path[i][0]), gui.canvas_y(api_rooms.room.position.y + path[i][1]));
        ctx.lineTo(gui.canvas_x(api_rooms.room.position.x + path[i+1][0]), gui.canvas_y(api_rooms.room.position.y + path[i+1][1]));
        ctx.stroke();
    }

/*    ctx.strokeStyle = "rgb(200,200,200)";
    ctx.beginPath();
    ctx.moveTo(vector[0][0], vector[0][1]);
    ctx.lineTo(vector[1][0], vector[1][1]);
    ctx.stroke();*/
}

gui.draw_player_actor = function(ctx, actor)
{
    gui.draw_text_centered(0, - 17, actor.username, "green");

    if (actor.health)
        gui.draw_health(ctx, actor);

    ctx.strokeStyle = "rgb(0,255,0)";
    ctx.beginPath();
    ctx.arc(0, 0,10,0,Math.PI*2);
    ctx.closePath();
    ctx.stroke();
}

gui.draw_npc_actor = function(ctx, actor)
{
    var textcolor = actor.visible ? "white" : "gray";
    gui.draw_text_centered(0, - 17, actor.actor_type + ": " + actor.script,
        textcolor);
    if (actor.exception)
        gui.draw_text_centered(0, - 27, actor.exception, "red");

    if (actor.health)
        gui.draw_health(ctx, actor);

    if (actor.visible)
        ctx.strokeStyle = "rgb(255,255,255)";
    else
        ctx.strokeStyle = "rgb(100,100,100)";
    ctx.beginPath();
    ctx.arc(0, 0,10,0,Math.PI*2);
    ctx.closePath();
    ctx.stroke();
}


gui.draw_health = function(ctx, actor)
{
    var left = - 13;
    var top = + 16;
    gui.fill_rect(left + 1, top + 1, 26 * actor.health, 3, "rgb(255, 255, 255)");
    gui.draw_rect(left, top, 26, 5, "rgb(150,250,150)");
}

gui.draw_actor = function(actor)
{
    try{
        if (actor.actor_type == 'player')
            gui.draw_player_actor(gui.ctx, actor);
        else
            gui.draw_npc_actor(gui.ctx, actor);
    }catch(e)
    {
        console.log("error: "+e);
    }
}

// -------- Util functions
gui.optionalRedraw = function(until_time)
{
    if (gui.redraw_until <= until_time)
    {
        gui.redraw_until = until_time;
        gui.requestRedraw();
    }
}

gui.actorRedraw = function()
{
    var until_time = api_rooms.get_now();
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (actor.vector.end_time * 1000 > until_time)
        {
            until_time = actor.vector.end_time * 1000
        }
    }
    if (until_time > api_rooms.get_now())
    {
        console.log("optionalRedraw() until " + new Date(until_time));
        gui.optionalRedraw(until_time);
    }
}

gui.requestRedraw = function()
{
    if (gui.redraw_timeout == null)
    {
        gui.redraw_timeout = setTimeout(gui.draw, 50);
    }
}


gui.draw_rect = function(x, y, width, height, color)
{
    gui.ctx.strokeStyle = color;
    gui.ctx.beginPath();
    gui.ctx.rect(x, y, width, height);
    gui.ctx.closePath();
    gui.ctx.stroke();
}

gui.fill_rect = function(x, y, width, height, color)
{
    gui.ctx.fillStyle = color;
    gui.ctx.fillRect(x, y, width, height);
}

gui.draw_text_centered = function(x, y, text, color)
{
    gui.ctx.font="10px Arial";
    if (color)
        gui.ctx.fillStyle = color;
    var metrics = gui.ctx.measureText(text);
    var width = metrics.width;
    gui.ctx.fillText(text, x - width / 2, y);
}

gui.fill_text_centered = function(x, y, text, color, fillColor)
{
    gui.ctx.font="10px Arial";
    if (color == null) color = "#000000";
    if (fillColor == null) fillColor = "#ffffff";
    var metrics = gui.ctx.measureText(text);
    var width = metrics.width;
    gui.ctx.fillStyle=fillColor;
    gui.ctx.fillRect(x - width / 2 - 5, y - 15, width + 10, 15);
    gui.ctx.fillStyle=color;
    gui.ctx.fillText(text, x - width / 2, y - 5);
}

gui.draw_circle = function(center_x, center_y, radius, color)
{
    if (color == null) color = "#ff0000";
    gui.ctx.beginPath();
    gui.ctx.arc(center_x, center_y, radius, 0, 2 * Math.PI, false);
    gui.ctx.strokeStyle = color;
    gui.ctx.stroke(); 
}

gui.fill_circle = function(center_x, center_y, radius, color)
{
    if (color == null) color = "#ff0000";
    gui.ctx.beginPath();
    gui.ctx.arc(center_x, center_y, radius, 0, 2 * Math.PI, false);
    gui.ctx.fillStyle = color;
    gui.ctx.fill(); 
}

gui.draw_line = function(x1, y1, x2, y2, color)
{
    if (color == null) color = "#ff0000";

    gui.ctx.beginPath();
    gui.ctx.moveTo(x1, y1);
    gui.ctx.lineTo(x2, y2);
    gui.ctx.strokeStyle = color;
    gui.ctx.stroke();

}
