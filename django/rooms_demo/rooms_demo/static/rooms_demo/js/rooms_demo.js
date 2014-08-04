
var rooms_demo = angular.module("RoomsDemo", ['ngRoute']);

rooms_demo.controller("GamesCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        console.log("Show Games");         
        $scope.playing_games = [];
        $scope.managed_games = [];
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
    }]);


rooms_demo.config(['$routeProvider',
    function($routeProvider) {
        $routeProvider.
            when('/games', {
                templateUrl: '/static/rooms_demo/html/games.html',
                controller: 'GamesCtrl'
            }).
            otherwise({
                redirectTo: '/games'
            });
    }]);


rooms_demo.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';    }
]);
