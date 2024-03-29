

var rooms_mapeditor = {};


rooms_mapeditor.all_maps = [];
rooms_mapeditor.selected_map = null;
rooms_mapeditor.map_data = {};
rooms_mapeditor.grid = 1.0;
rooms_mapeditor.grid_enabled = false;

rooms_mapeditor.selected_room = {'data': null};
rooms_mapeditor.selected_object = null;
rooms_mapeditor.selected_rooms_list = [];
rooms_mapeditor.selected_objects_list = [];

rooms_mapeditor.editable_object = null;

rooms_mapeditor.state = '';

rooms_mapeditor.undo_stack = [];
rooms_mapeditor.redo_stack = [];


rooms_mapeditor.has_editable_position = function() {
    return rooms_mapeditor.editable_object && 'position' in rooms_mapeditor.editable_object;
}

rooms_mapeditor.has_editable_object = function() {
    return rooms_mapeditor.editable_object && rooms_mapeditor.selected_room && rooms_mapeditor.selected_room.data.room_objects.indexOf(rooms_mapeditor.editable_object) != -1;
}

rooms_mapeditor.has_editable_door = function() {
    return rooms_mapeditor.editable_object && rooms_mapeditor.selected_room && rooms_mapeditor.selected_room.data.doors.indexOf(rooms_mapeditor.editable_object) != -1;
}

rooms_mapeditor.has_editable_tag = function() {
    return rooms_mapeditor.editable_object && rooms_mapeditor.selected_room && rooms_mapeditor.selected_room.data.tags.indexOf(rooms_mapeditor.editable_object) != -1;
}

rooms_mapeditor.push_undo = function() {
    rooms_mapeditor.undo_stack.push(JSON.parse(JSON.stringify(rooms_mapeditor.map_data)));
    rooms_mapeditor.redo_stack = [];
}

rooms_mapeditor.pop_undo = function() {
    if (rooms_mapeditor.undo_stack.length > 0) {
        var last_undo = JSON.parse(JSON.stringify(rooms_mapeditor.undo_stack.pop()));
        var previous_undo = JSON.parse(JSON.stringify(rooms_mapeditor.undo_stack[rooms_mapeditor.undo_stack.length-1]));
        if (previous_undo != undefined) {
            rooms_mapeditor.redo_stack.push(JSON.parse(JSON.stringify(rooms_mapeditor.map_data)));
            rooms_mapeditor.map_data = previous_undo;
        }
        turtlegui.reload();
    }
}

rooms_mapeditor.pop_redo = function() {
    if (rooms_mapeditor.redo_stack.length > 0) {
        rooms_mapeditor.map_data = JSON.parse(JSON.stringify(rooms_mapeditor.redo_stack.pop()));
        rooms_mapeditor.undo_stack.push(JSON.parse(JSON.stringify(rooms_mapeditor.map_data)));
        turtlegui.reload();
    }
}


rooms_mapeditor.load_maps = function() {
    $.ajax("/rooms_mapeditor/maps", {
        "dataType": "json",
        "success": function(data) {
            rooms_mapeditor.all_maps = data;
            if (rooms_mapeditor.all_maps) {
                rooms_mapeditor.selected_map = rooms_mapeditor.all_maps[0];
            }
            console.log("Loaded maps");
            turtlegui.reload();
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
            rooms_mapeditor.reload();
            rooms_mapeditor.push_undo();
        },
        cache: false
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

rooms_mapeditor.position_new_room = function () {
    rooms_mapeditor.state = 'positioning_new_room';
    turtlegui.reload();
}

rooms_mapeditor.create_room = function() {
    console.log("Create room");
    var room_id = prompt("Enter new room ID");
    if (room_id in rooms_mapeditor.map_data.rooms || room_id == "") {
        alert("Room ID already exists");
    }
    else {
        rooms_mapeditor.map_data.rooms[room_id] = {
            "info": {  },
            "position": { "x": gui.viewport_x * gui.zoom, "y": gui.viewport_y * gui.zoom},
            "width": 50 * gui.zoom,
            "height": 50 * gui.zoom,
            "room_objects": [],
            "tags": [],
            "doors": []
        };
        rooms_mapeditor.push_undo();
    }
};

rooms_mapeditor.create_object = function() {
    console.log("Create object");
    if (rooms_mapeditor.selected_room.data == null)
        return alert("No room selected");
    var object_type = prompt("Enter new object type");
    rooms_mapeditor.selected_room.data.room_objects[rooms_mapeditor.selected_room.data.room_objects.length] = {
        "object_type": object_type,
        "position": { "x": gui.viewport_x - rooms_mapeditor.selected_room.data.position.x, "y": gui.viewport_y - rooms_mapeditor.selected_room.data.position.y },
        "width": 20 * gui.zoom,
        "height": 20 * gui.zoom
    };
    rooms_mapeditor.push_undo();
};

rooms_mapeditor.create_door = function() {
    console.log("Create Door");
    if (rooms_mapeditor.selected_room.data == null)
        return alert("No room selected");
    var exit_id = prompt("Enter exit room id");
    var exit_position = prompt("Enter exit position (comma separated)");
    var exit_arr = exit_position.split(',');
    var exit_x = parseFloat(exit_arr[0]);
    var exit_y = parseFloat(exit_arr[1]);

    rooms_mapeditor.selected_room.data.doors[rooms_mapeditor.selected_room.data.doors.length] = {
        "position": { "x": gui.viewport_x - rooms_mapeditor.selected_room.data.position.x, "y": gui.viewport_y - rooms_mapeditor.selected_room.data.position.y },
        "exit_position": {"x": exit_x, "y": exit_y, "z": 0.0},
        "exit_room_id": exit_id,
        "width": 20 * gui.zoom,
        "height": 20 * gui.zoom
    };
    rooms_mapeditor.push_undo();
};


rooms_mapeditor.create_tag = function() {
    console.log("Create tag");
    if (rooms_mapeditor.selected_room.data == null)
        return alert("No room selected");
    var tag_type = prompt("Enter new tag type");
    rooms_mapeditor.selected_room.data.tags[rooms_mapeditor.selected_room.data.tags.length] = {
        "tag_type": tag_type,
        "position": { "x": gui.viewport_x - rooms_mapeditor.selected_room.data.position.x, "y": gui.viewport_y - rooms_mapeditor.selected_room.data.position.y},
        "data": { }
    };
    rooms_mapeditor.push_undo();
};

rooms_mapeditor.delete = function() {
    if (rooms_mapeditor.selected_object && rooms_mapeditor.selected_object == rooms_mapeditor.selected_room.data)
    {
        if (confirm("Delete room?"))
        {
            // delete room
            delete rooms_mapeditor.map_data.rooms[rooms_mapeditor.selected_room.room_id];
            rooms_mapeditor.reload();
            rooms_mapeditor.push_undo();
        }
    }
    else if (rooms_mapeditor.selected_object && rooms_mapeditor.selected_object == rooms_mapeditor.selected_object)
    {
        if (confirm("Delete object?"))
        {
            // delete object
            var index = rooms_mapeditor.selected_room.data.room_objects.indexOf(rooms_mapeditor.selected_object);
            if (index != -1) {
                var removed = rooms_mapeditor.selected_room.data.room_objects.splice(index, 1);
                console.log("Removed object: ");
                console.log(removed);
                rooms_mapeditor.reload();
                rooms_mapeditor.push_undo();
            }
            var index = rooms_mapeditor.selected_room.data.tags.indexOf(rooms_mapeditor.selected_object);
            if (index != -1) {
                var removed = rooms_mapeditor.selected_room.data.tags.splice(index, 1);
                console.log("Removed tag: ");
                console.log(removed);
                rooms_mapeditor.reload();
                rooms_mapeditor.push_undo();
            }
            var index = rooms_mapeditor.selected_room.data.doors.indexOf(rooms_mapeditor.selected_object);
            if (index != -1) {
                var removed = rooms_mapeditor.selected_room.data.doors.splice(index, 1);
                console.log("Removed door: ");
                console.log(removed);
                rooms_mapeditor.reload();
                rooms_mapeditor.push_undo();
            }

        }
    }
};

rooms_mapeditor.toggle_grid = function(enable) {
    
}

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

rooms_mapeditor.get_editable_data = function() {
    var data_str = JSON.stringify(rooms_mapeditor.editable_object.data, null, 4);
    if (data_str)
        return data_str;
    else
        return "";
}

rooms_mapeditor.set_editable_data = function(data_text) {
    rooms_mapeditor.editable_object.data = JSON.parse(data_text.replace(/\n/g, " "));
    rooms_mapeditor.push_undo()
}

rooms_mapeditor.format_json = function(data) {
    return JSON.stringify(data, null, 4);
}


rooms_mapeditor.undo_keypress = function(e) {
      if( e.which === 90 && e.ctrlKey && e.shiftKey ){
         console.log('control + shift + z'); 
         rooms_mapeditor.pop_redo();
         return false;
      }
      else if( e.which === 90 && e.ctrlKey ){
         console.log('control + z'); 
         rooms_mapeditor.pop_undo();
         return false;	
      }          
}; 

rooms_mapeditor.reload = function() {
    turtlegui.reload();
    $(':input').change(rooms_mapeditor.push_undo);
};


rooms_mapeditor.button_enabled = function(buttonid) {
    if (rooms_mapeditor.state == '') return 'enabled';
    if (buttonid == 'newroom' && rooms_mapeditor.state == 'positioning_new_room') return 'enabled';
    return 'disabled';
}


$(document).ready(function() {
    console.log("Loading");
    rooms_mapeditor.load_maps();
    rooms_mapeditor.reload();
	$(document).keydown(rooms_mapeditor.undo_keypress);
});
