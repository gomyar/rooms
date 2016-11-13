
var admin = {};

admin.data = {
    tab: 'nodes',
    nodes: []
};


admin.load_nodes = function() {
    $.get('/admin/list_nodes', function(data, status) {
        admin.data.nodes = data;        
        turtlegui.reload();
    });
}

admin.load_games= function() {
    $.get('/admin/list_games', function(data, status) {
        admin.data.games = data;        
        turtlegui.reload();
    });
}

admin.load_rooms = function() {
    $.get('/admin/list_rooms', function(data, status) {
        admin.data.rooms = data;        
        turtlegui.reload();
    });
}

admin.show_node_rooms = function(node) {
    console.log("Node: " + node.name);
    $.get('/admin/list_rooms?node_name='+node.name, function(data, status) {
        for (n in admin.data.nodes) {
            var nnode = admin.data.nodes[n];
            if (nnode.name == node.name) {
                nnode.rooms = data;
            }
        }
        turtlegui.reload();
    });
}

admin.show_game_rooms = function(game) {
    console.log("game: " + game.game_id);
    $.get('/admin/list_rooms?game_id='+game.game_id, function(data, status) {
        for (n in admin.data.games) {
            var ngame = admin.data.games[n];
            if (ngame.game_id == game.game_id) {
                ngame.rooms = data;
            }
        }
        turtlegui.reload();
    });
}

admin.switch_tab = function(tab) {
    admin.data.tab = tab;
    turtlegui.reload();
}

admin.room_connect = function(room) {
    console.log("Connect: " + node.name + " - " + room.room_id);
    $.post('/master/connect_admin', {game_id:room.game_id, room_id:room.room_id}, function(data, status) {
        var token = data.token;
        var host = data.host;
        window.open('/adminfiles/html/admin_game_client.html?token=' + token + '&node_host=' + host, '_blank');
    });
}

admin.show_nodes = function() {
    admin.data.tab = 'nodes';
    admin.load_nodes();
}

admin.show_games = function() {
    admin.data.tab = 'games';
    admin.load_games();
}

admin.show_rooms = function() {
    admin.data.tab = 'rooms';
    admin.load_rooms();
}

$( document ).ready(function() {
    admin.show_nodes();
});
