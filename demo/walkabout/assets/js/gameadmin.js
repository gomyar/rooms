
var gameAdminControllers = angular.module("gameAdminControllers", []);

gameAdminControllers.controller("AdminCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        $http.get("/master/all_games").success(function(data) {
            $scope.games = data;
            $scope.games.select = function(game) {
                console.log("Selected " + game);
                $http.post("/player/join_game/" + $scope.username + "/" + game.game_id + "/" + $scope.room_id).success(function(data) {
                    console.log("Joined game successfully");
                    console.log(data);
                    $location.path('/games/' + game.game_id);
                });
            };
        });
}]);
