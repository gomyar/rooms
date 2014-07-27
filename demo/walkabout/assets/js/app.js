
window.onerror = function (errorMsg, url, lineNumber, columnNumber, errorObject) {
    if (errorObject && /<omitted>/.test(errorMsg)) {
        console.error('Full exception message: ' + errorObject.message);
    }
}

var gameAdminApp = angular.module("gameAdminApp", [
    'ngRoute',
    'gameControllers',
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


