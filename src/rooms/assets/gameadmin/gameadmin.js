
window.onerror = function (errorMsg, url, lineNumber, columnNumber, errorObject) {
    if (errorObject && /<omitted>/.test(errorMsg)) {
        console.error('Full exception message: ' + errorObject.message);
    }
}

var gameAdminApp = angular.module("gameAdminApp", [
    'ngRoute',
    'gameAdminControllers'
]);

gameAdminApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/games', {
        templateUrl: 'admin.html',
        controller: 'AdminCtrl'
      }).
      when('/games/:game_id', {
        templateUrl: 'game.html',
        controller: 'GameCtrl'
      }).
      otherwise({
        redirectTo: '/games'
      });
  }]);

var gameAdminControllers = angular.module("gameAdminControllers", []);

gameAdminControllers.controller("AdminCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        $http.get("/master/all_games").success(function(data) {
            $scope.games = data;
            $scope.games.select = function(game) {
                console.log("Selected " + game);
                $location.path('/games/' + game.game_id);
            };
        });
}]);

gameAdminControllers.controller("GameCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
       console.log("init game");         
}]);


