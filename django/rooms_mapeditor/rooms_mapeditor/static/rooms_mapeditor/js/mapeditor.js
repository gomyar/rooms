
var mapeditor = angular.module("RoomsMapEditor", ['ngRoute']);

mapeditor.controller("MapEditCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        console.log("Show Maps");
        $scope.all_maps = [];
        $http.get("/rooms_mapeditor/maps").success(function(data) {
            $scope.all_maps = data;
            $scope.selected_map = null;
        });

        $scope.load_selected_map = function() {
            $http.get("/rooms_mapeditor/maps/" + $scope.selected_map).success(function(data) {
                $scope.current_map = data;
                gui.init($('#screen')[0]);
            });
        };
    }]);

