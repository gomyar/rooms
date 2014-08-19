
var rooms_demo = angular.module("RoomsDemo", ['ngRoute']);

rooms_demo.controller("GamesCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        console.log("Show Games");         
        $scope.playing_games = [];
        $scope.available_games = [];
        $scope.managed_games = [];
        $scope.games = {};
        $scope.games.create = function(data) {
            console.log("Create");
            $location.path("/create_game");
        };
        $scope.games.join_game = function(game_id) {
            console.log("Joining");
            console.log($scope.create_params);
            $location.path("/join_game/" + game_id);
        };
        $scope.games.play_game = function(game_id) {
            console.log("Playing");
            $location.path("/play_game/" + game_id);
        };
        $scope.games.end_game = function(game_id) {
            console.log("ending");
            alert("Ending game: "+game_id+ " (unimplemented)");
        };
        $http.get("/rooms_demo/playing_games").success(function(data) {
            $scope.playing_games = data;
            $scope.playing_games.select = function(game) {
                console.log("Selected playing" + game);
                console.log(game);
            };
        });
        $http.get("/rooms_demo/available_games").success(function(data) {
            $scope.available_games = data;
            $scope.available_games.select = function(game) {
                console.log("Selected available" + game);
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


rooms_demo.controller("JoinGameCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.game_id = $routeParams.game_id;
        $scope.player_join_game = function(data) {
            $http.post("/rooms_demo/join_game/" + $scope.game_id, $scope.create_params).success(
                function(data) {
                    console.log("Joined");
                    $location.path("/rooms_demo/games");
                }
            );
        };
        $scope.create_params = {};
        $http.get("/rooms_demo/game_create_params").success(function(data) {
            console.log("Got params");
            console.log(data);
            for (var key in data)
                $scope.create_params[data[key]] = "";
        });
    }]);


rooms_demo.controller("PlayGameCtrl", ['$scope', '$http', '$location',
        '$routeParams',
    function($scope, $http, $location, $routeParams) {
        $scope.game_id = $routeParams.game_id;
        init_game($scope.game_id, username);
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
            when('/join_game/:game_id', {
                templateUrl: '/static/rooms_demo/html/join_game.html',
                controller: 'JoinGameCtrl'
            }).
            when('/play_game/:game_id', {
                templateUrl: '/static/rooms_demo/html/play_game.html',
                controller: 'PlayGameCtrl'
            }).
            otherwise({
                redirectTo: '/games'
            });
    }]);


rooms_demo.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';    }
]);
