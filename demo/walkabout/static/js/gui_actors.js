
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
    gui.ctx.strokeStyle = 'green';
    gui.ctx.arc(0, 0, gui.zoom * 10, 0, 2 * Math.PI, false);
}

gui_actors.draw_npc_actor = function(actor)
{
    gui.ctx.strokeStyle = 'white';
    gui.ctx.arc(0, 0, gui.zoom * 10, 0, 2 * Math.PI, false);
}

gui_actors.actor_draw_funcs = {
    'player': gui_actors.draw_player_actor,
    'npc': gui_actors.draw_npc_actor
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
