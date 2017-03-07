
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
gui.door_hovered = null;
gui.actor_hovered = null;
gui.following_actor = null;

gui.debug = {"mouse_at": [0, 0]};

gui.initCanvas = function(canvas)
{
    gui.canvas = canvas;
    $(window).resize(function() { gui.resetCanvas(); gui.draw(); });
    gui.resetCanvas();
}

gui.resetCanvas = function()
{
    gui.ctx = gui.canvas.getContext("2d");
    var parent = $(gui.canvas).parent();
    gui.canvas.width = parent.width();
    gui.canvas.height = parent.height();

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
    gui.check_viewport();
    gui.redraw_timeout = null;
    gui.ctx.clearRect(0, 0, gui.canvas.width, gui.canvas.height);

    gui_room.draw_room();
    gui_actors.draw_actors();

    gui.draw_debug();

    var nowish = api_rooms.get_now();
    if (nowish < gui.redraw_until)
        gui.requestRedraw();
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
    drawutils.draw_text_centered(50, 20, "("+parseInt(gui.viewport_x)+", "+parseInt(gui.viewport_y)+")", "white");
    drawutils.draw_text_centered(75, 50, "canvas("+parseInt(gui.canvas_left())+", "+parseInt(gui.canvas_top())+", "+parseInt(gui.canvas_right())+","+parseInt(gui.canvas_bottom())+")", "white");
    drawutils.draw_text_centered(50, 80, "Zoom:" + Math.round(gui.zoom*100)/100, "white");
    drawutils.draw_text_centered(50, 110, "MouseAt:" + Math.round(gui.debug.mouse_at[0] * 100)/100 + ", "+Math.round(gui.debug.mouse_at[1] * 100)/100, "white");
}

gui.check_viewport = function()
{
    if (gui.following_actor)
    {
        gui.viewport_x = gui.following_actor.x();
        gui.viewport_y = gui.following_actor.y();
    }
}
