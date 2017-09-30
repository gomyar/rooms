
var gui_room = {}

gui_room.draw_room = function()
{
    if (!api_rooms.room) return;

    gui.ctx.strokeStyle = "rgb(0, 255, 255)";
    var x = api_rooms.room.topleft.x;
    var y = api_rooms.room.topleft.y;
    var width = api_rooms.room.bottomright.x - x;
    var height = api_rooms.room.bottomright.y - y;
    gui.ctx.strokeRect(gui.canvas_x(x), gui.canvas_y(y), width / gui.zoom, height / gui.zoom)

    // Draw room objects
    for (var object_id in api_rooms.room.room_objects)
    {
        var room_object = api_rooms.room.room_objects[object_id];
        gui.ctx.save();
        gui.ctx.translate(gui.canvas_x(room_object.topleft.x), gui.canvas_y(room_object.topleft.y));
        gui_room.draw_room_object(room_object);
        gui.ctx.restore();
    }

    // Draw doors
    for (var i in api_rooms.room.doors)
    {
        var door = api_rooms.room.doors[i];
        gui.ctx.save();
        gui.ctx.translate(gui.canvas_x(door.enter_position.x), gui.canvas_y(door.enter_position.y));
        gui_room.draw_door(door);
        gui.ctx.restore();
    }
}

gui_room.draw_door = function(door)
{
    drawutils.draw_circle(0, 0, 20 / gui.zoom, "#0011ff");
    if (door == gui.door_hovered)
    {
        drawutils.draw_circle(0, 0, 22 / gui.zoom, "#00ffff");
    }
}

gui_room.draw_rect = function(room_object)
{
    var x = room_object.topleft.x;
    var y = room_object.topleft.y;
    var width = room_object.bottomright.x - x;
    var height = room_object.bottomright.y - y;
    gui.ctx.strokeRect(0, 0, width / gui.zoom, height / gui.zoom)
}

gui_room.object_draw_funcs = {
    'rect': gui_room.draw_rect
};

gui_room.draw_room_object = function(room_object)
{
    if (room_object.object_type in gui_room.object_draw_funcs)
        gui_room.object_draw_funcs[room_object.object_type](room_object);
    else
        gui_room.object_draw_funcs['rect'](room_object);
}

gui_room.door_at = function(x, y)
{
    for (var i in api_rooms.room.doors)
    {
        var door = api_rooms.room.doors[i];
        var door_x = door.enter_position.x;
        var door_y = door.enter_position.y;
        if (door_x + 20 > x && door_x - 20 < x &&
            door_y + 20 > y && door_y - 20 < y)
            return door;
    }
    return null;
}
