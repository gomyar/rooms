
var gui = {};

gui.canvas = null;
gui.ctx = null;

gui.redraw_until = 0;
gui.walk_timeout = 0;
gui.redraw_timeout = null;

gui.viewport_x = 0;
gui.viewport_y = 0;
gui.zoom = 1.0;

gui.selected_actor = null;

gui.initCanvas = function(canvas)
{
    gui.canvas = canvas;
    $(window).resize(function() { gui.resetCanvas(); gui.draw(); });
    gui.resetCanvas();
}

gui.resetCanvas = function()
{
    gui.ctx = gui.canvas.getContext("2d");
    gui.requestRedraw();
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
    gui.ctx.clearRect(0, 0, gui.canvas.width, gui.canvas.height);

    gui.draw_room();
    gui.draw_actors();

    gui.draw_debug();

    var nowish = api_rooms.get_now();
    if (nowish < gui.redraw_until)
        gui.requestRedraw();
}

gui.draw_room = function()
{
    gui.ctx.strokeStyle = "rgb(0, 255, 255)";
    var x = api_rooms.room.topleft.x;
    var y = api_rooms.room.topleft.y;
    var width = api_rooms.room.bottomright.x - x;
    var height = api_rooms.room.bottomright.y - y;
    gui.ctx.strokeRect(gui.canvas_x(x), gui.canvas_y(y), width / gui.zoom, height / gui.zoom)

    // Draw room objects
    for (object_id in api_rooms.room.room_objects)
    {
        var room_object = api_rooms.room.room_objects[object_id];
        var x = room_object.topleft.x;
        var y = room_object.topleft.y;
        var width = room_object.bottomright.x - x;
        var height = room_object.bottomright.y - y;
        gui.ctx.drawImage(guiassets.images[room_object.object_type], gui.canvas_x(x), gui.canvas_y(y), width / gui.zoom, height / gui.zoom);
    }
}

gui.draw_actors = function()
{
    // Draw actors
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        gui.ctx.save();
        gui.ctx.translate(gui.canvas_x(actor.x()), gui.canvas_y(actor.y()));
        gui.draw_actor(actor);
        gui.ctx.restore();
    }
}

gui.draw_player_actor = function(ctx, actor)
{
    var img = guiassets.images[actor.model_type];
    var width = img.width / gui.zoom;
    var height = img.width / gui.zoom;
    ctx.rotate(Math.atan2(actor.vector.end_pos.y - actor.vector.start_pos.y,
        actor.vector.end_pos.x - actor.vector.start_pos.x));
    var offset = 0;
    if (actor.vector.end_time * 1000 > api_rooms.get_now())
        offset = Math.round((api_rooms.get_now() - actor.vector.start_time * 1000) / 400) % Math.round(img.height / img.width) * img.width;
    ctx.drawImage(img, 0, offset, img.width, img.width, -(width / 2), -(height / 2), width, height);
}

gui.actor_draw_funcs = {
    'player': gui.draw_player_actor
};

gui.draw_actor = function(actor)
{
    gui.actor_draw_funcs[actor.actor_type](gui.ctx, actor);
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
    gui.check_viewport();
    if (gui.redraw_timeout == null)
    {
        gui.redraw_timeout = setTimeout(gui.draw, 50);
    }
}

gui.draw_debug = function()
{
    guiutils.draw_text_centered(50, 20, "("+parseInt(gui.viewport_x)+", "+parseInt(gui.viewport_y)+")", "white");
    guiutils.draw_text_centered(75, 50, "canvas("+parseInt(gui.canvas_left())+", "+parseInt(gui.canvas_top())+", "+parseInt(gui.canvas_right())+","+parseInt(gui.canvas_bottom())+")", "white");
    guiutils.draw_text_centered(50, 80, "Zoom:" + Math.round(gui.zoom*100)/100, "white");
}

gui.check_viewport = function()
{
    if (gui.following_actor)
    {
        gui.viewport_x = gui.following_actor.x();
        gui.viewport_y = gui.following_actor.y();
    }
}
