
var mapeditor = angular.module("RoomsMapEditor", ['ngRoute']);

mapeditor.controller("MapEditCtrl", ['$scope', '$http', '$location',
    function($scope, $http, $location) {
        console.log("Show Maps");
        $scope.all_maps = [];
        $scope.selected_map = null;
        $scope.load_maps = function() {
            $http.get("/rooms_mapeditor/maps").success(function(data) {
                $scope.all_maps = data;
            });
        };
        $scope.load_maps();

        $scope.load_selected_map = function() {
            $http.get("/rooms_mapeditor/maps/" + $scope.selected_map).success(function(data) {
                $scope.current_map = data;
                // center view on map data
                gui.init($('#screen')[0]);
                gui.center_view(data);
            });
        };

        $scope.create_map = function() {
            var map_id = prompt("Enter new map ID");
            if (map_id in $scope.all_maps)
                alert("Map ID already exists");
            else
                if (map_id)
                {
                    $http.post("/rooms_mapeditor/maps", {map_id: map_id}).success(function(data) {
                        $scope.load_maps();
                        $scope.selected_map = map_id;
                        $scope.load_selected_map();
                    });
                }
        };
    }]);



mapeditor.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';    }
]);

