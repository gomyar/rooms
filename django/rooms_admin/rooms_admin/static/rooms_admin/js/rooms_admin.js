
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
    }]);


rooms_admin.controller("RoomsInGameCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.game_id = $routeParams.game_id;
        console.log("Show rooms in game: " + $routeParams.game_id);         
    }]);


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
            otherwise({
                redirectTo: '/nodes'
            });
    }]);
