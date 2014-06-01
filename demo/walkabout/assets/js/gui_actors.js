
var gui_actors = {}

gui_actors.draw_actors = function()
{
    // Draw actors
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        gui.ctx.save();
        gui.ctx.translate(gui.canvas_x(actor.x()), gui.canvas_y(actor.y()));
        gui_actors.draw_actor(actor);
        gui.ctx.restore();
    }
}

gui_actors.draw_player_actor = function(actor)
{
    var img = guiassets.images[actor.actor_type];
    var width = img.width / gui.zoom;
    var height = img.width / gui.zoom;
    gui.ctx.rotate(Math.atan2(actor.vector.end_pos.y - actor.vector.start_pos.y,
        actor.vector.end_pos.x - actor.vector.start_pos.x));
    var offset = 0;
    if (actor.vector.end_time * 1000 > api_rooms.get_now())
        offset = Math.round((api_rooms.get_now() - actor.vector.start_time * 1000) / 400) % Math.round(img.height / img.width) * img.width;
    gui.ctx.drawImage(img, 0, offset, img.width, img.width, -(width / 2), -(height / 2), width, height);
}

gui_actors.actor_draw_funcs = {
    'player': gui_actors.draw_player_actor
};

gui_actors.draw_actor = function(actor)
{
    gui_actors.actor_draw_funcs[actor.actor_type](actor);
}

gui_actors.actor_at = function(x, y)
{
    for (var i in api_rooms.actors)
    {
        var actor = api_rooms.actors[i];
        if (actor.x() + 20 > x && actor.x() - 20 < x &&
            actor.y() + 20 > y && actor.y() - 20 < y)
            return actor;
    }
    return null;
}
