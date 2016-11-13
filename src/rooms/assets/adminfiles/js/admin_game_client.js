
var admin = {
    actor_list: [],
    selected_actor: null
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


admin.load_room = function(room_id) {
    console.log("Load room" + room_id);
}


admin.game_callback = function(message) {
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
        admin.load_room(message.data.room_id);
        gui.zoom = 0.1;
        gui.requestRedraw();
        turtlegui.reload();
    }
}


admin.admin_connect = function(node_host, token)
{
    api_rooms.admin_connect(node_host, token, admin.game_callback);
}


$( document ).ready(function() {
    admin.admin_connect(getUrlParameter('node_host'), getUrlParameter('token'));
});
