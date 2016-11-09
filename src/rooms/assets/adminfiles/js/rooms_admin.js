

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

admin.switch_tab = function(tab) {
    admin.data.tab = tab;
    turtlegui.reload();
}

admin.room_connect = function(node, room) {
    console.log("Connect: " + node.name + " - " + room.room_id);
}


$( document ).ready(function() {
    admin.load_nodes();
});
