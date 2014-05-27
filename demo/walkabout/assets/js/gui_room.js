
var gui_room = {}

gui_room.draw_room = function()
{
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
        gui.ctx.translate(gui.canvas_x(api_rooms.room.topleft.x + room_object.topleft.x), gui.canvas_y(api_rooms.room.topleft.y + room_object.topleft.y));
        gui_room.draw_room_object(room_object);
        gui.ctx.restore();
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
    gui_room.object_draw_funcs[room_object.object_type](room_object);
}

