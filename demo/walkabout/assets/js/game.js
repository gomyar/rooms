
var gameControllers = angular.module("gameControllers", []);

gameControllers.controller("GameCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
       console.log("init game");         
       init_game();
}]);
