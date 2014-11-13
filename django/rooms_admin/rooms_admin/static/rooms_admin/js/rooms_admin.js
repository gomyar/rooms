
var rooms_admin = angular.module("RoomsAdmin", ['ngRoute']);

rooms_admin.controller("NodesCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        console.log("Show Nodes");         
        $scope.registered_nodes = [];
        $http.get("/rooms_admin/all_nodes").success(function(data) {
            $scope.registered_nodes = data;
            $scope.registered_nodes.select = function(node) {
                console.log("Selected " + node);
                console.log(node);
                $location.path("/rooms_on_node/" + node.host + "/" + node.port);
            };
        });
    }]);

rooms_admin.controller("GamesCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        console.log("Show games");         
    }]);


rooms_admin.controller("RoomsOnNodeCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.nodeHost = $routeParams.nodeHost;
        $scope.nodePort = $routeParams.nodePort;
        console.log("Show rooms on node : " + $scope.nodeHost + ":" + $scope.nodePort);         
        $scope.rooms = [];
        $http.get("/rooms_admin/all_rooms_on_node/" + $scope.nodeHost + "/" + $scope.nodePort).success(function(data) {
            $scope.rooms = data;
            $scope.rooms.select = function(room) {
                console.log("Selected " + room);
                console.log(room);
                $location.path("/admin_game_client/" + room.game_id + "/" + room.room_id);
            };
        });
    }]);


rooms_admin.controller("RoomsInGameCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.game_id = $routeParams.game_id;
        $scope.rooms = [];
        console.log("Show rooms in game: " + $routeParams.game_id);
    }]);


rooms_admin.controller("AdminGameClientCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.game_id = $routeParams.game_id;
        $scope.room_id = $routeParams.room_id;
        console.log("Show rooms in game: " + $scope.game_id + "-"+ $scope.room_id);         
        var token = $http.post("/rooms_admin/request_admin_token",
            {"game_id": $scope.game_id, "room_id": $scope.room_id}
            ).success(
            function (data) {
                console.log("got token");
                console.log(data);
                api_rooms.admin_connect(data.node[0], data.node[1],
                    data.token, game_callback);
                gui.init($('#screen')[0]);
            }
            );

    }]);


rooms_admin.controller("ItemRegistryCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.items = [
            {"category": "test", "item_type": "type"},
            {"category": "test", "item_type": "type"},
            {"category": "test", "item_type": "type"},
            {"category": "test", "item_type": "type"}
        ];
        $scope.current = {
            "category": "",
            "item_type": "",
            "fields" : [
                {"name": "", "value": ""}
            ]
        };
        $scope.new_field = function() {
            $scope.current.fields[$scope.current.fields.length] = {"name": "", "value": ""}
        };
        $scope.delete_field = function(index) {
            $scope.current.fields.splice(index, 1);
        };
        $http.get("/rooms_admin/all_items/").success(function(items) {
            $scope.items = items;
        });
        $scope.item_save = function() {
            var token = $http.post("/rooms_admin/save_item/", $scope.current 
                ).success(
                function (data) {
                    console.log("saved item");
                }
            );
        };
        console.log("Show items");
    }]);


rooms_admin.controller("NewItemCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.category = "new cateogry"; 
        $scope.item_type = "new type"; 
        $scope.data = {
            "field1": "value1",
            "field2": "value2"
        };
        $scope.item_save = function() {
        var itemdata = $scope.data;
        itemdata['category'] = $scope.category;
        itemdata['item_type'] = $scope.item_type;
        var token = $http.post("/rooms_admin/save_item/", itemdata
            ).success(
            function (data) {
                console.log("saved item");
            }
            );

           
        };
        $scope.item_cancel = function() {
        };
    }]);



function game_callback(msg)
{
    if (msg.command == "map_loaded")
    {
        console.log("Loaded map");
        console.log(msg);
    }
    if (msg.command == "actor_update")
    {
        var end_time = api_rooms.actors[msg.data.actor_id].vector.end_time * 1000;
        gui.requestRedraw();
    }
    if (msg.command == "remove_actor")
    {
        gui.requestRedraw();
    }
    if (msg.command == "sync")
    {
        load_room(msg.data.room_id);
        api_rooms.vision = msg.data.vision;
        gui.requestRedraw();
    }
}


perform_get = function(url, callback, onerror)
{
    $.ajax({
        'url': url,
        'success': function(data) {
            if (callback != null)
                callback(data);
        },
        'error': function(jqXHR, errorText) {
            console.log("Error calling "+url+" : "+errorText);
            if (onerror)
                onerror(errorText, jqXHR);
        },
        'type': 'GET'
    });
}

function load_room(room_id)
{
    var map_id = room_id.split('.')[0];

    // TODO: Might send this right through the admin api
    perform_get("http://" + api_rooms.node_host + ":" + api_rooms.node_port + "/node_game/admin_map/" + api_rooms.token + "/" + map_id,
        function(data){ show_room(data, room_id);},
        function(errTxt, jqXHR){ alert("Error loading room: "+errTxt);});
}


function show_room(data, room_id)
{
    api_rooms.room = data['rooms'][room_id];
    api_rooms.room_map = data['rooms'];
    gui.viewport_x = (api_rooms.room.topleft.x + api_rooms.room.bottomright.x) / 2;
    gui.viewport_y = (api_rooms.room.topleft.y + api_rooms.room.bottomright.y) / 2;
    gui.zoom = 1.2 * (api_rooms.room.bottomright.y - api_rooms.room.topleft.y) / gui.canvas.height;
    gui.requestRedraw();
}



rooms_admin.config(['$routeProvider',
    function($routeProvider) {
        $routeProvider.
            when('/nodes', {
                templateUrl: '/static/rooms_admin/html/nodes.html',
                controller: 'NodesCtrl'
            }).
            when('/games', {
                templateUrl: '/static/rooms_admin/html/games.html',
                controller: 'GamesCtrl'
            }).
            when('/items', {
                templateUrl: '/static/rooms_admin/html/items.html',
                controller: 'ItemRegistryCtrl'
            }).
            when('/rooms_on_node/:nodeHost/:nodePort', {
                templateUrl: '/static/rooms_admin/html/rooms.html',
                controller: 'RoomsOnNodeCtrl'
            }).
            when('/rooms_in_game/:game_id', {
                templateUrl: '/static/rooms_admin/html/rooms.html',
                controller: 'RoomsInGameCtrl'
            }).
            when('/admin_game_client/:game_id/:room_id', {
                templateUrl: '/static/rooms_admin/html/admin_game_client.html',
                controller: 'AdminGameClientCtrl'
            }).
            otherwise({
                redirectTo: '/nodes'
            });
    }]);


rooms_admin.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';    }
]);