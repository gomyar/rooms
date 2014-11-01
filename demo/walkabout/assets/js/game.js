
var gameControllers = angular.module("gameControllers", []);

gameControllers.controller("GameCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location, $routeParams) {
       console.log("init game");         
       init_game($routeParams.game_id, $.routeParams.username, $routeParams.token);
}]);
