
var gameControllers = angular.module("gameControllers", []);

gameControllers.controller("GameCtrl", ['$scope', '$http', '$location',
        '$cookieStore',
    function($scope, $http, $location, $cookieStore) {
       console.log("init game");         
       init_game($cookieStore.get("game_id"), $cookieStore.get("username"), $cookieStore.get("token"));
}]);
