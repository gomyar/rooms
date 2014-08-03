
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


function game_callback(msg)
{
    console.log("Recieved message:" + msg.command);
    console.log(msg);
    if (msg.command == "map_loaded")
    {
        console.log("Loaded map");
    }
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
