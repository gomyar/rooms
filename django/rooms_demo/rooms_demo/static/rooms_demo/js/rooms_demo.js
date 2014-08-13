
var rooms_demo = angular.module("RoomsDemo", ['ngRoute']);

rooms_demo.controller("GamesCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        console.log("Show Games");         
        $scope.playing_games = [];
        $scope.managed_games = [];
        $scope.games = {};
        $scope.create_params = {};
        $http.get("/rooms_demo/game_create_params").success(function(data) {
            console.log("Got params");
            console.log(data);
            for (var key in data)
                $scope.create_params[data[key]] = "";
        });
        $scope.games.create = function(data) {
            console.log("Create");
            $location.path("/create_game");
        };
        $scope.games.join_game = function(data) {
            console.log("Joining");
            console.log($scope.create_params);
        };
        $http.get("/rooms_demo/playing_games").success(function(data) {
            $scope.playing_games = data;
            $scope.playing_games.select = function(game) {
                console.log("Selected playing" + game);
                console.log(game);
            };
        });
        $http.get("/rooms_demo/managed_games").success(function(data) {
            $scope.managed_games = data;
            $scope.managed_games.select = function(game) {
                console.log("Selected managed" + game);
                console.log(game);
            };
        });
        $scope.games.is_playing = function(game_id) {
            for (var i in $scope.playing_games) {
                var player = $scope.playing_games[i];
                if (player.game_id == game_id)
                    return true;
            };
            return false;
        };
    }]);


rooms_demo.controller("CreateGameCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        $scope.game = {};
        $scope.game.confirm = function(data) {
            console.log("Confirmed");
            $http.post("/rooms_demo/create_game", {}).success(function(data) {
                console.log("created");
                // go somewhere
                $location.path("/games");
            });
        };
        $scope.game.cancel = function(data) {
            $location.path("/games");
        };
    }]);


rooms_demo.config(['$routeProvider',
    function($routeProvider) {
        $routeProvider.
            when('/games', {
                templateUrl: '/static/rooms_demo/html/games.html',
                controller: 'GamesCtrl'
            }).
            when('/create_game', {
                templateUrl: '/static/rooms_demo/html/create_game.html',
                controller: 'CreateGameCtrl'
            }).
            otherwise({
                redirectTo: '/games'
            });
    }]);


rooms_demo.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';    }
]);
