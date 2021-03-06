
var admin = {};

admin.data = {
    tab: 'nodes',
    nodes: []
};

admin.update_state_key = null;
admin.update_state_json = null;


admin.load_nodes = function() {
    $.get('/rooms_admin/nodes', function(data, status) {
        admin.data.nodes = data;        
        turtlegui.reload();
    });
}

admin.load_games= function() {
    $.get('/rooms_admin/games', function(data, status) {
        admin.data.games = data;        
        turtlegui.reload();
    });
}

admin.load_rooms = function() {
    $.get('/rooms_admin/rooms', function(data, status) {
        admin.data.rooms = data;        
        turtlegui.reload();
    });
}

admin.show_node_rooms = function(node) {
    console.log("Node: " + node.name);
    $.get('/rooms_admin/rooms?node_name='+node.name, function(data, status) {
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
    $.get('/rooms_admin/rooms?game_id='+game.game_id, function(data, status) {
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
    window.open('/rooms_admin/game_client/' + room.game_id + '/' + room.room_id, '_blank');
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

admin.describe_health = function(node) {
    return node.healthy ? 'healthy' : 'unhealthy';
}

$( document ).ready(function() {
    admin.show_nodes();
});
