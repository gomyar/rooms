
var gameAdminControllers = angular.module("gameAdminControllers", []);

gameAdminControllers.controller("AdminCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        $http.get("/master_control/all_games").success(function(data) {
            $scope.games = data;
            $scope.games.select = function(game) {
                console.log("Selected " + game);
                $http.post("/master_game/join_game/" + $scope.username + "/" + game.game_id + "/" + $scope.room_id).success(function(data) {
                    console.log("Joined game successfully");
                    console.log(data);
                    $location.path('/play/'+data.token+'/'+$scope.username+'/'+$scope.room_id+'/'+game.game_id);
                });
            };
        });
}]);
