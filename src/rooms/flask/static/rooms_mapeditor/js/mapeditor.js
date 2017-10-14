

var rooms_mapeditor = {};


rooms_mapeditor.all_maps = [];
rooms_mapeditor.selected_map = null;
rooms_mapeditor.map_data = {};
rooms_mapeditor.grid = 1.0;

rooms_mapeditor.selected_room = {'data': null};
rooms_mapeditor.selected_object = null;
rooms_mapeditor.selected_rooms_list = [];
rooms_mapeditor.selected_rooms_list_x = 0;
rooms_mapeditor.selected_rooms_list_y = 0;
rooms_mapeditor.selected_objects_list = [];
rooms_mapeditor.selected_objects_list_x = 0;
rooms_mapeditor.selected_objects_list_y = 0;


rooms_mapeditor.load_maps = function() {
    $.ajax("/rooms_mapeditor/maps", {
        "dataType": "json",
        "success": function(data) {
            rooms_mapeditor.all_maps = data;
            turtlegui.reload();
            console.log("Loaded maps");
        }
    });
};

rooms_mapeditor.load_selected_map = function() {
    $.ajax("/rooms_mapeditor/maps/" + rooms_mapeditor.selected_map, {
        "dataType": "json",
        "success": function(data) {
            rooms_mapeditor.map_data = data;
            // center view on map data
            gui.init($('#screen')[0]);
            gui.center_view(data);
        }
    });
};

rooms_mapeditor.create_map = function() {
    var map_id = prompt("Enter new map ID");
    if (map_id in rooms_mapeditor.all_maps || map_id == "")
        alert("Map ID already exists");
    else
        if (map_id)
        {
            $.ajax("/rooms_mapeditor/maps", {
                "data": JSON.stringify({map_id: map_id}),
                "method": "POST",
                "dataType": "json",
                "contentType": "application/json; charset=utf-8",
                "success": function(data) {
                    rooms_mapeditor.load_maps();
                    rooms_mapeditor.selected_map = map_id;
                    rooms_mapeditor.load_selected_map();
                }
            });
        }
};


rooms_mapeditor.map_selected = function() {
    var map_id = $(this).val();
    rooms_mapeditor.selected_map = map_id;
    rooms_mapeditor.load_selected_map();
}

rooms_mapeditor.save_map = function() {
    if (confirm("Save current map data to : " + rooms_mapeditor.map_data.map_id +" ?"))
    {
        $.ajax("/rooms_mapeditor/maps", {
            "data": JSON.stringify({map_data: rooms_mapeditor.map_data}),
            "method": "PUT",
            "dataType": "json",
            "contentType": "application/json; charset=utf-8",
            "success": function() {
                alert("Map saved");
            }
        });
    }
};

rooms_mapeditor.create_room = function() {
    console.log("Create room");
    var room_id = prompt("Enter new room ID");
    if (room_id in rooms_mapeditor.map_data.rooms || room_id == "")
        alert("Room ID already exists");
    else
        rooms_mapeditor.map_data.rooms[room_id] = {
            "info": {  },
            "topleft": { "x": gui.viewport_x - 50 * gui.zoom, "y": gui.viewport_y - 50 * gui.zoom},
            "bottomright": { "x": gui.viewport_x + 50 * gui.zoom, "y": gui.viewport_y + 50 * gui.zoom},
            "room_objects": [],
            "tags": [],
            "doors": []
        };
};

rooms_mapeditor.create_object = function() {
    console.log("Create object");
    if (rooms_mapeditor.selected_room.data == null)
        return alert("No room selected");
    var object_type = prompt("Enter new object type");
    rooms_mapeditor.selected_room.data.room_objects[rooms_mapeditor.selected_room.data.room_objects.length] = {
        "object_type": object_type,
        "topleft": { "x": gui.viewport_x - rooms_mapeditor.selected_room.data.topleft.x - 20 * gui.zoom, "y": gui.viewport_y - rooms_mapeditor.selected_room.data.topleft.y - 20 * gui.zoom},
        "bottomright": { "x": gui.viewport_x - rooms_mapeditor.selected_room.data.topleft.x + 20 * gui.zoom, "y": gui.viewport_y - rooms_mapeditor.selected_room.data.topleft.y + 20 * gui.zoom}
    };
};

rooms_mapeditor.create_tag = function() {
    console.log("Create tag");
    if (rooms_mapeditor.selected_room.data == null)
        return alert("No room selected");
    var tag_type = prompt("Enter new tag type");
    rooms_mapeditor.selected_room.data.tags[rooms_mapeditor.selected_room.data.tags.length] = {
        "tag_type": tag_type,
        "position": { "x": gui.viewport_x - rooms_mapeditor.selected_room.data.topleft.x - 20 * gui.zoom, "y": gui.viewport_y - rooms_mapeditor.selected_room.data.topleft.y - 20 * gui.zoom},
        "data": { }
    };
};

rooms_mapeditor.delete = function() {
    if (rooms_mapeditor.selected_object && rooms_mapeditor.selected_object == rooms_mapeditor.selected_room.data)
    {
        if (confirm("Delete room?"))
        {
            // delete room
            delete rooms_mapeditor.map_data.rooms[rooms_mapeditor.selected_room.room_id];
        }
    }
    else if (rooms_mapeditor.selected_object && rooms_mapeditor.selected_object == rooms_mapeditor.selected_object)
    {
        if (confirm("Delete object?"))
        {
            // delete object
            var index = rooms_mapeditor.selected_room.data.room_objects.indexOf(rooms_mapeditor.selected_object);
            var removed = rooms_mapeditor.selected_room.data.room_objects.splice(index, 1);
            console.log("Removed: ");
            console.log(removed);
        }
    }
};

rooms_mapeditor.highlight_object = function(obj) {
    gui.highlighted_objects=[obj];
    gui.requestRedraw();
};

rooms_mapeditor.select_room = function(room_id) {
    console.log("Selecting room " + room_id);
    rooms_mapeditor.selected_room = {"room_id": room_id, "data": rooms_mapeditor.map_data.rooms[room_id]};
    rooms_mapeditor.selected_rooms_list = [];

    rooms_mapeditor.editable_object = rooms_mapeditor.map_data.rooms[room_id];
    rooms_mapeditor.selected_object = null;
};

rooms_mapeditor.select_object = function(obj) {
    console.log("Selecting object " + obj.object_type);
    rooms_mapeditor.selected_object = obj;
    rooms_mapeditor.selected_objects_list=[];

    rooms_mapeditor.editable_object = obj;
};

rooms_mapeditor.set_position = function(pos, x, y) {
    pos.x = x - x % rooms_mapeditor.grid;
    pos.y = y - y % rooms_mapeditor.grid;
};

$(document).ready(function() {
    console.log("Loading");
    turtlegui.reload();
    rooms_mapeditor.load_maps();
});
