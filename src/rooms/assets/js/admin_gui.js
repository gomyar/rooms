
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


gui.init_input = function()
{
    $(gui.canvas).click(gui.canvas_clicked);
    $(gui.canvas).mousemove(gui.canvas_mousemove);
    $(gui.canvas).mousedown(gui.canvas_mousedown);
    $(gui.canvas).mouseup(gui.canvas_mouseup);
    $(gui.canvas).mouseover(gui.canvas_mouseover);
    $(gui.canvas).mouseout(gui.canvas_mouseout);
    $(gui.canvas).mousewheel(gui.canvas_mousewheel);
}


gui.canvas_clicked = function(e)
{
    if (!gui.swallow_click)
    {
        var click_x = gui.real_x(e.clientX);
        var click_y = gui.real_y(e.clientY);

        actor = gui.find_actor(click_x, click_y);
        if (actor)
            gui.select_actor(actor);
        else 
            gui.walk_to(click_x, click_y)
    }
    gui.swallow_click = false;
}

gui.canvas_mousemove = function(e)
{
    if (gui.mouse_down)
    {
        var moved_x = gui.move_start_x - e.clientX
        var moved_y = gui.move_start_y - e.clientY;
        gui.viewport_x += moved_x * gui.zoom;
        gui.viewport_y += moved_y * gui.zoom;
        gui.move_start_x = e.clientX;
        gui.move_start_y = e.clientY;

        if (Math.abs(moved_x) > 1 || Math.abs(moved_y) > 1)
            gui.swallow_click = true;

        gui.requestRedraw();
    }
    else
    {
        var click_x = gui.real_x(e.clientX);
        var click_y = gui.real_y(e.clientY);

        var actors = gui.find_all_actors_at(click_x, click_y);
        if (actors.length > 0)
        {
            $(gui.canvas).css('cursor', 'pointer');
            gui.selected_actor = actors[0];
            gui.show_actor_list(actors);
            gui.requestRedraw();
        }
        else
        {
            $(gui.canvas).css('cursor', 'auto');
            gui.selected_actor = null;
            $('.actor_list').remove();
            gui.requestRedraw();
        }
    }
}

gui.show_actor_list = function(actors)
{
    // show list of selected actors
    $(".actor_list").remove();
    var actor_list = div("actor_list");
    for (var i in actors)
    {
        var actor = actors[i];
        actor_list.append(
            div('actor', {'text': actor.name})
        );
    }
    $("#main").append(actor_list);
}

gui.canvas_mousedown = function(e)
{
    gui.mouse_down = true;
    gui.move_start_x = e.clientX;
    gui.move_start_y = e.clientY;

    if ($(".mapcontrol").size() > 0)
        gui.swallow_click = true;
}

gui.canvas_mouseup = function(e)
{
    gui.mouse_down = false;
}

gui.canvas_mousewheel = function(e, delta, deltaX, deltaY)
{
    var start_x = gui.real_x(e.clientX);
    var start_y = gui.real_y(e.clientY);
    gui.zoom += gui.zoom * 0.1 * -deltaY;

    var end_x = gui.real_x(e.clientX);
    var end_y = gui.real_y(e.clientY);
    var moved_x = start_x - end_x;
    var moved_y = start_y - end_y;
    gui.viewport_x += moved_x;
    gui.viewport_y += moved_y;

    gui.requestRedraw();
}

gui.canvas_clicked = function(e)
{
    if (!gui.swallow_click)
    {
        var click_x = gui.real_x(e.clientX);
        var click_y = gui.real_y(e.clientY);

        actor = gui.find_actor(click_x, click_y);
        if (actor)
            gui.select_actor(actor);
        else 
            gui.walk_to(click_x, click_y)
    }
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


gui.at_position = function(actor, x, y)
{
    x1 = actor.x() - 12 * gui.zoom;
    y1 = actor.y() - 12 * gui.zoom;
    x2 = x1 + 25 * gui.zoom;
    y2 = y1 + 25 * gui.zoom;
    return x > x1 && x < x2 && y > y1 && y < y2;
}


// Actor movey selecty
gui.select_actor = function(actor)
{
    gui.selected_actor = actor;
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




// ----------------- ols gui.js

gui.resetCanvas = function()
{
    gui.canvas.width = $("#main").width();
    gui.canvas.height = $("#main").height();
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

gui.draw_room = function()
{
    for (object_id in api_rooms.room.map_objects)
    {
        var map_object = api_rooms.room.map_objects[object_id];
        gui.ctx.drawImage(map_object.img, map_object.position[0], map_object.position[1], map_object.width, map_object.height);
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
    console.log("Drawing");
    gui.redraw_timeout = null;
    gui.ctx.fillStyle = "rgb(0,0,0)";
    gui.ctx.clearRect(0, 0, gui.canvas.width, gui.canvas.height);

    gui.ctx.strokeStyle = "rgb(255, 255, 255)";
    gui.ctx.strokeRect(gui.canvas_x(0), gui.canvas_y(0), gui.canvas_x(api_rooms.room.width)-gui.canvas_x(0), gui.canvas_y(api_rooms.room.height)-gui.canvas_y(0))

    gui.draw_vision_grid();

    // Draw room objects
    for (object_id in api_rooms.room.map_objects)
    {
        var map_object = api_rooms.room.map_objects[object_id];
        gui.draw_rect(
            gui.canvas_x(map_object.position[0]),
            gui.canvas_y(map_object.position[1]),
            map_object.width / gui.zoom,
            map_object.height / gui.zoom,
            "rgb(0, 255, 0)"
        );
//        gui.ctx.drawImage(map_object.img, gui.canvas_x(map_object.position[0]), gui.canvas_y(map_object.position[1]), map_object.width / gui.zoom, map_object.height / gui.zoom);
    }

    // Draw actors
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        gui.ctx.save();
        gui.ctx.translate(gui.canvas_x(actor.x()), gui.canvas_y(actor.y()));
        gui.draw_actor(actor);
        gui.ctx.restore();

        gui.draw_path(gui.ctx, actor.path);
    }
    if (gui.selected_actor)
        gui.draw_rect(gui.canvas_x(gui.selected_actor.x()) - 15, gui.canvas_y(gui.selected_actor.y()) - 15, 32, 32, "rgb(150,250,150)");

    gui.draw_text_centered(50, 20, "("+parseInt(gui.viewport_x)+", "+parseInt(gui.viewport_y)+")", "white");
    gui.draw_text_centered(75, 50, "canvas("+parseInt(gui.canvas_left())+", "+parseInt(gui.canvas_top())+", "+parseInt(gui.canvas_right())+","+parseInt(gui.canvas_bottom())+")", "white");
    gui.draw_text_centered(50, 80, "Zoom:" + Math.round(gui.zoom*100)/100, "white");


    var nowish = api_rooms.get_now();
    if (nowish < gui.redraw_until)
        gui.requestRedraw();
}


gui.draw_vision_grid = function()
{
    var gridsize = api_rooms.room.visibility_grid.gridsize;
    var width = api_rooms.room.visibility_grid.width;
    var height = api_rooms.room.visibility_grid.height;
    for (var x=0; x<width; x += gridsize)
        gui.draw_line(gui.canvas_x(x), gui.canvas_y(0), gui.canvas_x(x), gui.canvas_y(height), "#111111");
    for (var y=0; y<height; y += gridsize)
        gui.draw_line(gui.canvas_x(0), gui.canvas_y(y), gui.canvas_x(width), gui.canvas_y(y), "#111111");
    for (var actor_id in api_rooms.room.visibility_grid.actors)
    {
        var blip = api_rooms.room.visibility_grid.actors[actor_id];
        gui.fill_circle(gui.canvas_x(blip[0] * gridsize), gui.canvas_y(blip[1] * gridsize), 2, "#ffffff");

    }
}


// ------ actor draw functions
gui.draw_path = function(ctx, path)
{
    ctx.strokeStyle = "rgb(0,0,200)";
    for (var i=0;i<path.length-1;i++)
    {
        ctx.beginPath();
        ctx.arc(gui.canvas_x(path[i+1][0]), gui.canvas_y(path[i+1][1]),10,0,Math.PI*2);
        ctx.closePath();
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(gui.canvas_x(path[i][0]), gui.canvas_y(path[i][1]));
        ctx.lineTo(gui.canvas_x(path[i+1][0]), gui.canvas_y(path[i+1][1]));
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
    gui.draw_text_centered(0, - 17, actor.name, "white");

    if (actor.health)
        gui.draw_health(ctx, actor);

    ctx.strokeStyle = "rgb(255,255,255)";
    ctx.beginPath();
    ctx.arc(0, 0,10,0,Math.PI*2);
    ctx.closePath();
    ctx.stroke();
}

gui.draw_npc_actor = function(ctx, actor)
{
//    console.log("Drawing npc at "+actor.x() +","+actor.y());
 //   console.log("Drawing real at "+gui.canvas_x(actor.x()) +","+gui.canvas_y(actor.y()));
    gui.draw_text_centered(0, - 17, actor.name, "white");

    if (actor.health)
        gui.draw_health(ctx, actor);

    ctx.strokeStyle = "rgb(0,0,255)";
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
    var until_time = Math.max(api_rooms.get_now(), api_rooms.player_actor.end_time());
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (actor.end_time() > until_time)
            until_time = actor.end_time()
    }
    if (until_time > api_rooms.get_now())
        gui.optionalRedraw(until_time);
}

gui.requestRedraw = function()
{
    if (gui.redraw_timeout == null)
        gui.redraw_timeout = setTimeout(gui.draw, 50);
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
