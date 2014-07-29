
var gameAdminControllers = angular.module("gameAdminControllers", []);

gameAdminControllers.controller("AdminCtrl", ['$scope', '$http', '$location',
        '$cookieStore',
    function($scope, $http, $location, $cookieStore) {
        $http.get("/master/all_games").success(function(data) {
            $scope.games = data;
            $scope.games.select = function(game) {
                console.log("Selected " + game);
                $http.post("/player/join_game/" + $scope.username + "/" + game.game_id + "/" + $scope.room_id).success(function(data) {
                    console.log("Joined game successfully");
                    console.log(data);
                    $cookieStore.put('token', data.token);
                    $cookieStore.put('username', $scope.username);
                    $cookieStore.put('room_id', $scope.room_id);
                    $cookieStore.put('game_id', game.game_id);
                    $location.path('/play');
                });
            };
        });
}]);
