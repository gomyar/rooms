
var admin = {
    actor_list: [],
    selected_actor: null,
    mapdata: {},
    geography: {type: 'none', polygons: []}
};


// Thank you Stackoverflow
var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};


admin.select_actor = function(actor) {
    admin.selected_actor = actor;
    turtlegui.reload();
}


admin.load_room = function(room_id) {
    console.log("Load room" + room_id);
    var map_id = room_id.split('.')[0];

    $.get("/rooms_admin/maps/" + map_id + ".json").success(function(data) {
        admin.mapdata = data;
        api_rooms.room = data['rooms'][room_id];
        gui.center_on_room();
        gui.requestRedraw();
    });
}

admin.kick_actor = function(actor_id) {
    $.post("/rooms_admin/game_client/" + game_id + "/" + room_id + "/" + actor_id + "/kick", {});
}


admin.game_callback = function(message) {
    console.log("Callback:");
    console.log(message);
    gui.actorRedraw();
    if (message.command == "actor_update")
    {
        gui.requestRedraw(api_rooms.actors[message.data.actor_id].vector.end_time * 1000);
        turtlegui.reload();
    }
    if (message.command == "remove_actor")
    {
        gui.requestRedraw();
        turtlegui.reload();
    }
    if (message.command == "message")
    {
        console.log(message);
    }
    if (message.command == "sync")
    {
        gui.init($('#screen')[0]);
        admin.load_room(message.data.room_id);
        admin.geography = message.geography;
        gui.zoom = 1.0;
        turtlegui.reload();
    }
}

admin.actor_fields_filter = function() {
    return ['actor_id', 'username', 'visible', 'docked_with', 'path', 'state'];
}

admin.format_field = function(actor, field_name) {
    return JSON.stringify(actor[field_name], null, 4);

}


admin.admin_connect = function(game_id, room_id)
{
    api_rooms.connect('/rooms_admin/connect/'+game_id + "/" + room_id, admin.game_callback);
}


$( document ).ready(function() {
    admin.admin_connect(game_id, room_id);
});
