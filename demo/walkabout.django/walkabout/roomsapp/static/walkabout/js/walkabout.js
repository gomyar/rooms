
var game = {
    actor_list: [],
    selected_actor: null,
    mapdata: {}
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



game.load_room = function(room_id) {
    console.log("Load room" + room_id);
    var map_id = room_id.split('.')[0];

    $.get("/admin/room_map/" + map_id).success(function(data) {
        game.mapdata = data;
        api_rooms.room = data['rooms'][room_id];
        gui.requestRedraw();
    });
}


game.game_callback = function(message) {
    console.log("Callback:");
    console.log(message);
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
        game.load_room(message.data.room_id);
        gui.zoom = 1.0;
        turtlegui.reload();
    }
}


game.connect = function(game_id)
{
    $.post('/master/connect_admin', {game_id:game_id}, function(data, status) {
        var token = data.token;
        var host = data.host;
        api_rooms.connect(host, token, game.game_callback);
    });
}


$( document ).ready(function() {
    api_rooms.connect('localhost:9999', getUrlParameter('game_id'), game.game_callback);
});
