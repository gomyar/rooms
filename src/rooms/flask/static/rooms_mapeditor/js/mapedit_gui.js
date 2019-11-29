
var gui = {};

gui.canvas = null;
gui.ctx = null;

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

gui.redraw_until = null;
gui.redraw_timeout = null;

gui.highlighted_rooms = [];
gui.highlighted_objects = [];

gui.dragging_editable = false;

TAG_WIDTH = 50;
TAG_HEIGHT = 50;

gui.init = function(canvas)
{
    gui.canvas = canvas;

    $(gui.canvas).click(gui.canvas_clicked);
    $(gui.canvas).mousemove(gui.canvas_mousemove);
    $(gui.canvas).mousedown(gui.canvas_mousedown);
    $(gui.canvas).mouseup(gui.canvas_mouseup);
    $(gui.canvas).mouseover(gui.canvas_mouseover);
    $(gui.canvas).mouseout(gui.canvas_mouseout);
    $(gui.canvas).mousewheel(gui.canvas_mousewheel);

    $(window).resize(function() { gui.resetCanvas(); gui.draw(); });
    gui.resetCanvas();
}


gui.center_view = function(map_data)
{
    var x1 = null;
    var y1 = null;
    var x2 = null;
    var y2 = null;

    for (var room_id in map_data.rooms)
    {
        var room = map_data.rooms[room_id];
        if (room.position.x - room.width / 2 < x1 || x1 == null) x1 = room.position.x - room.width / 2;
        if (room.position.y - room.height / 2 < y1 || y1 == null) y1 = room.position.y - room.height / 2;
        if (room.position.x + room.width / 2 > x2 || x2 == null) x2 = room.position.x + room.width / 2;
        if (room.position.y + room.height / 2 > y2 || y2 == null) y2 = room.position.y + room.height / 2 ;
    }
    gui.viewport_x = (x1 + x2) / 2;
    gui.viewport_y = (y1 + y2) / 2;
    gui.zoom = 1.2 * (y2 - y1) / gui.canvas.height;
    gui.requestRedraw();
}

gui.set_position = function(pos, x, y) {
    var p = gui.grid_correct(x, y);
    pos.x = p[0];
    pos.y = p[1];
};

gui.grid_correct = function(x, y) {
    if (rooms_mapeditor.grid_enabled) {
        return [x - x % rooms_mapeditor.grid,
                y - y % rooms_mapeditor.grid];
    } else {
        return [x - 1,
                y - 1];
    }
}

gui.canvas_mousemove = function(e)
{
    gui.mouse_client_x = (e.clientX - $(gui.canvas).offset().left);
    gui.mouse_client_y = (e.clientY - $(gui.canvas).offset().top);

    if (gui.mouse_down)
    {
        var moved_x = gui.move_start_x - (e.clientX - $(gui.canvas).offset().left)
        var moved_y = gui.move_start_y - (e.clientY - $(gui.canvas).offset().top);
        if (gui.dragging_editable && e.ctrlKey)
        {
            var moved = gui.grid_correct(
                gui.draggable_start_position_x - (moved_x) * gui.zoom,
                gui.draggable_start_position_y - (moved_y) * gui.zoom);
            var new_x = moved[0];
            var new_y = moved[1];

            var resized = gui.grid_correct(
                gui.draggable_start_width - (moved_x * 2) * gui.zoom,
                gui.draggable_start_height - (moved_y * 2) * gui.zoom);
            var new_width = resized[0];
            var new_height = resized[1];

            rooms_mapeditor.editable_object.position.x = new_x;
            rooms_mapeditor.editable_object.position.y = new_y;
            rooms_mapeditor.editable_object.width = new_width;
            rooms_mapeditor.editable_object.height = new_height;
        }
        else if (gui.dragging_editable)
        {
            gui.set_position(rooms_mapeditor.editable_object.position,
                gui.draggable_start_position_x - moved_x * gui.zoom,
                gui.draggable_start_position_y - moved_y * gui.zoom);
        }
        else
        {
            gui.viewport_x = gui.move_viewport_start_x + moved_x * gui.zoom;
            gui.viewport_y = gui.move_viewport_start_y + moved_y * gui.zoom;
        }

        if (Math.abs(moved_x) > 1 || Math.abs(moved_y) > 1)
            gui.swallow_click = true;
    }
    else
    {
        var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
        var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));

        // if room not selected, and room clicked, select room
        gui.highlighted_rooms = gui.find_rooms_at(click_x, click_y);
        gui.highlighted_objects = gui.find_objects_at(click_x, click_y);
    }
    gui.requestRedraw();
}

gui.canvas_mousedown = function(e)
{
    gui.mouse_down = true;
    gui.move_start_x = (e.clientX - $(gui.canvas).offset().left);
    gui.move_start_y = (e.clientY - $(gui.canvas).offset().top);
    gui.move_viewport_start_x = gui.viewport_x;
    gui.move_viewport_start_y = gui.viewport_y;
    var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
    var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));

    gui.dragging_editable = gui.is_editable_drag_at(click_x, click_y);
    if (gui.dragging_editable)
    {
        gui.draggable_start_position_x = rooms_mapeditor.editable_object.position.x;
        gui.draggable_start_position_y = rooms_mapeditor.editable_object.position.y;
        gui.draggable_start_width = rooms_mapeditor.editable_object.width;
        gui.draggable_start_height = rooms_mapeditor.editable_object.height;
    }

    if ($(".mapcontrol").size() > 0)
        gui.swallow_click = true;
}

gui.is_editable_drag_at = function(click_x, click_y)
{
    var room_at = gui.find_rooms_at(click_x, click_y)[rooms_mapeditor.selected_room.room_id];
    var objects_at = gui.find_objects_at(click_x, click_y);
    return rooms_mapeditor.editable_object != null && (objects_at.indexOf(rooms_mapeditor.editable_object) != -1 || rooms_mapeditor.editable_object == room_at);
}

gui.canvas_mouseup = function(e)
{
    if (gui.dragging_editable) {
        rooms_mapeditor.push_undo();
        rooms_mapeditor.reload();
    }
    gui.mouse_down = false;
    gui.dragging_editable = false;
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
    if (!gui.swallow_click)
    {
        var click_x = gui.real_x((e.clientX - $(gui.canvas).offset().left));
        var click_y = gui.real_y((e.clientY - $(gui.canvas).offset().top));


        if (gui.highlighted_objects.length == 1)
        {
            rooms_mapeditor.select_object(gui.highlighted_objects[0]);
        }
        else if (gui.highlighted_objects.length > 1)
        {
            rooms_mapeditor.selected_objects_list = gui.highlighted_objects;
            rooms_mapeditor.selected_objects_list_x = e.clientX;
            rooms_mapeditor.selected_objects_list_y = e.clientY;
        }

        // check room
        else if (Object.keys(gui.highlighted_rooms).length == 1)
        {
            var room_id = Object.keys(gui.highlighted_rooms)[0];
            rooms_mapeditor.select_room(room_id);
        }
        else if (Object.keys(gui.highlighted_rooms).length > 1)
        {
            rooms_mapeditor.selected_rooms_list = gui.highlighted_rooms;
            rooms_mapeditor.selected_rooms_list_x = e.clientX;
            rooms_mapeditor.selected_rooms_list_y = e.clientY;
        }
        else
        {
            rooms_mapeditor.select_room(null);
            rooms_mapeditor.selected_room = {data: null};
        }

        rooms_mapeditor.selected_rooms_list = [];
        rooms_mapeditor.reload();
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

gui.room_at = function(room, x, y)
{
    return x >= (room.position.x - room.width / 2) && y >= (room.position.y - room.height / 2) && x <= (room.position.x + room.width / 2) && y <= (room.position.y + room.height / 2);
}


gui.object_at = function(object, x, y)
{
    var room_x = rooms_mapeditor.selected_room.data.position.x;
    var room_y = rooms_mapeditor.selected_room.data.position.y;
    var left = room_x + (object.position.x - object.width / 2);
    var top = room_y + (object.position.y - object.height / 2);
    var right = room_x + (object.position.x + object.width / 2);
    var bottom = room_y + (object.position.y + object.height / 2);
    return x >= left && y >= top && x <= right && y <= bottom;
}


gui.door_at = function(door, x, y)
{
    var room_x = rooms_mapeditor.selected_room.data.position.x;
    var room_y = rooms_mapeditor.selected_room.data.position.y;
    return x >= room_x + (door.position.x - TAG_WIDTH / 2) && y >= room_y + (door.position.y - TAG_HEIGHT / 2) && x <= room_x + (door.position.x + TAG_WIDTH / 2) && y <= room_y + (door.position.y + TAG_HEIGHT / 2);
}


gui.tag_at = function(object, x, y)
{
    var room_x = rooms_mapeditor.selected_room.data.position.x;
    var room_y = rooms_mapeditor.selected_room.data.position.y;
    return x >= room_x + object.position.x - TAG_WIDTH / 2 && y >= room_y + object.position.y - TAG_HEIGHT / 2 && x <= room_x + object.position.x + TAG_HEIGHT / 2 && y <= room_y + object.position.y + TAG_HEIGHT / 2;
}


gui.get_selected_actor = function()
{
    return rooms_mapeditor.selected_actor;
}


gui.find_rooms_at = function(x, y)
{
    var rooms = {};
    var map_data = rooms_mapeditor.map_data;
    for (var room_id in map_data.rooms)
    {
        var room = map_data.rooms[room_id];
        if (gui.room_at(room, x, y))
            rooms[room_id] = room;
    }
    return rooms;
}


gui.find_objects_at = function(x, y)
{
    var objects = [];
    if (rooms_mapeditor.selected_room.data != null)
    {
        var room_objects = rooms_mapeditor.selected_room.data.room_objects;
        for (var object_id in room_objects)
        {
            var object = room_objects[object_id];
            if (gui.object_at(object, x, y))
                objects[objects.length] = object;
        }
        var room_tags = rooms_mapeditor.selected_room.data.tags;
        for (var tag_id in room_tags)
        {
            var tag = room_tags[tag_id];
            if (gui.tag_at(tag, x, y))
                objects[objects.length] = tag;
        }
        var room_doors = rooms_mapeditor.selected_room.data.doors;
        for (var door_id in room_doors)
        {
            var door = room_doors[door_id];
            if (gui.door_at(door, x, y))
                objects[objects.length] = door;
        }
    }
    return objects;
}


// ----------------- ols gui.js

gui.resetCanvas = function()
{
    gui.canvas.width = $("#screen").parent().width();
    gui.canvas.height = $("#screen").parent().height();
    gui.ctx=gui.canvas.getContext("2d");
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

gui.is_room_highlighted = function(room_id)
{
    for (var room_id in gui.highlighted_rooms)
        if (gui.highlighted_rooms[room_id].room_id == room_id)
            return true;
    return false;
}

gui.is_object_highlighted = function(object)
{
    for (var i in gui.highlighted_objects)
        if (gui.highlighted_objects[i] == object)
            return true;
    return false;
}


gui.is_tag_highlighted = function(tag)
{
    for (var i in gui.highlighted_tags)
        if (gui.highlighted_tags[i] == tag)
            return true;
    return false;
}


gui.draw = function()
{
    gui.redraw_timeout = null;
    gui.ctx.fillStyle = "rgb(0,0,0)";
    gui.ctx.clearRect(0, 0, gui.canvas.width, gui.canvas.height);

    // draw position crosshair
    var origin_x = gui.canvas_x(gui.viewport_x);
    var origin_y = gui.canvas_y(gui.viewport_y);
    gui.draw_line(origin_x, 0, origin_x, gui.canvas.height, "#303090");
    gui.draw_line(0, origin_y, gui.canvas.width, origin_y, "#303090");

    // draw origin crosshair
    var origin_x = gui.canvas_x(0);
    var origin_y = gui.canvas_y(0);
    gui.draw_line(origin_x, 0, origin_x, gui.canvas.height, "#606080");
    gui.draw_line(0, origin_y, gui.canvas.width, origin_y, "#606080");

    // Draw other rooms in map
    var map_data = rooms_mapeditor.map_data;
    for (var room_id in map_data.rooms)
    {
        var room = rooms_mapeditor.map_data.rooms[room_id];
        gui.ctx.strokeStyle = "rgb(100, 100, 255)";
        if (room_id in gui.highlighted_rooms)
            gui.ctx.strokeStyle = "rgb(255, 255, 255)";
        if (room == rooms_mapeditor.selected_room.data)
            gui.ctx.strokeStyle = "rgb(55, 255, 55)";
        var width = room.width;
        var height = room.height;
        var room_x = gui.canvas_x(room.position.x - width / 2);
        var room_y = gui.canvas_y(room.position.y - height / 2);
        gui.ctx.strokeRect(room_x, room_y, width / gui.zoom, height / gui.zoom)

        // draw if currently editing room
        if (room == rooms_mapeditor.editable_object) {
            gui.draw_rect(
                room_x - 10,
                room_y - 10,
                width / gui.zoom + 20,
                height / gui.zoom + 20,
                "#ff0000");
        }

        // Draw doors
        for (var door_index in room.doors)
        {
            var door = room.doors[door_index];

            var color = "rgb(55, 55, 255)";
            if (gui.is_object_highlighted(door))
                color = "rgb(200, 250, 150)";
            if (door == rooms_mapeditor.selected_object)
                color = "rgb(255, 255, 255)";
            gui.ctx.strokeStyle = color;
            gui.ctx.beginPath();
            gui.ctx.arc(gui.canvas_x(door.position.x + room.position.x), gui.canvas_y(door.position.y + room.position.y), 10, 0, Math.PI*2);
            gui.ctx.closePath();
            gui.ctx.stroke();

            if (door.exit_room_id in rooms_mapeditor.map_data.rooms) {
                var exit_room = rooms_mapeditor.map_data.rooms[door.exit_room_id];

                gui.ctx.beginPath();
                gui.ctx.arc(gui.canvas_x(door.exit_position.x + exit_room.position.x), gui.canvas_y(door.exit_position.y + exit_room.position.y), 5, 0, Math.PI*2);
                gui.ctx.closePath();
                gui.ctx.stroke();
    
                gui.ctx.beginPath();
                gui.ctx.moveTo(gui.canvas_x(door.position.x + room.position.x), gui.canvas_y(door.position.y + room.position.y));
                gui.ctx.lineTo(gui.canvas_x(door.exit_position.x + exit_room.position.x), gui.canvas_y(door.exit_position.y + exit_room.position.y));
                gui.ctx.stroke();
                
            }

        }

        // Draw room objects
        for (var object_id in room.room_objects)
        {
            var map_object = room.room_objects[object_id];
            var width = map_object.width;
            var height = map_object.height;
            var color = "rgb(150, 200, 50)";
            var object_x = gui.canvas_x(map_object.position.x - map_object.width / 2 + room.position.x);
            var object_y = gui.canvas_y(map_object.position.y - map_object.height / 2 + room.position.y);

            if (gui.is_object_highlighted(map_object))
                color = "rgb(200, 250, 150)";
            if (map_object == rooms_mapeditor.selected_object)
                color = "rgb(255, 255, 255)";
            width = Math.max(width, 2);
            height = Math.max(height, 2);
            gui.ctx.globalAlpha = 0.1;
            gui.fill_rect(
                object_x,
                object_y,
                width / gui.zoom,
                height / gui.zoom,
                color
            );
            gui.ctx.globalAlpha = 1.0;
            gui.draw_rect(
                object_x,
                object_y,
                width / gui.zoom,
                height / gui.zoom,
                color
            );
            var text_x = gui.canvas_x(map_object.position.x + room.position.x);
            gui.draw_text_centered(text_x, object_y + 10, map_object.object_type, color);

            // draw if currently editing object
            if (map_object == rooms_mapeditor.editable_object) {

                gui.draw_rect(
                    object_x,
                    object_y,
                    width / gui.zoom,
                    height / gui.zoom,
                    "#ff0000");
            }
        }

        // Draw tags
        for (tag_id in room.tags)
        {
            var map_tag = room.tags[tag_id];
            var width = TAG_WIDTH / gui.zoom;
            var height = TAG_HEIGHT / gui.zoom;
            var color = "rgb(150, 50, 200)";
            var tag_x = gui.canvas_x(map_tag.position.x - TAG_WIDTH / 2 + room.position.x);
            var tag_y = gui.canvas_y(map_tag.position.y - TAG_HEIGHT / 2 + room.position.y);

            if (gui.is_object_highlighted(map_tag))
                color = "rgb(200, 150, 250)";
            if (map_tag == rooms_mapeditor.selected_tag)
                color = "rgb(255, 255, 255)";
            gui.ctx.globalAlpha = 0.1;
            gui.fill_rect(
                tag_x,
                tag_y,
                width,
                height,
                color
            );
            gui.ctx.globalAlpha = 1.0;
            gui.draw_rect(
                tag_x,
                tag_y,
                width,
                height,
                color
            );

            gui.draw_text_centered(tag_x + width / 2, tag_y + 10, map_tag.tag_type, color);

            // draw if currency editing
            if (map_tag == rooms_mapeditor.editable_object) {
                if (gui.is_object_highlighted(map_tag))
                    color = "rgb(200, 50, 50)";
                if (map_tag == rooms_mapeditor.selected_tag)
                    color = "rgb(255, 55, 55)";
                gui.ctx.globalAlpha = 0.1;
                gui.fill_rect(
                    tag_x,
                    tag_y,
                    width,
                    height,
                    color
                );
                gui.ctx.globalAlpha = 1.0;
                gui.draw_rect(
                    tag_x,
                    tag_y,
                    width,
                    height,
                    color
                );
            }
        }
    }

    gui.draw_text_centered(50, 20, "Viewport: ("+parseInt(gui.viewport_x)+", "+parseInt(gui.viewport_y)+")", "white");
    gui.draw_text_centered(50, 40, "Position: ("+parseInt(gui.real_x(gui.mouse_client_x))+", "+parseInt(gui.real_y(gui.mouse_client_y))+")", "white");
    gui.draw_text_centered(50, 60, "Mouse: ("+parseInt(gui.mouse_client_x)+", "+parseInt(gui.mouse_client_y)+")", "white");
    gui.draw_text_centered(50, 80, "Zoom:" + Math.round(gui.zoom*100)/100, "white");

    var nowish = gui.get_now();
    if (nowish < gui.redraw_until)
        gui.requestRedraw();
}

gui.get_now = function()
{
    return new Date().getTime();
}


// ------ actor draw functions
gui.requestRedraw = function(redraw_until)
{
    if (redraw_until == null)
        redraw_until = gui.get_now() + 150;
    if (gui.redraw_until == null || gui.redraw_until < redraw_until)
        gui.redraw_until = redraw_until;
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
