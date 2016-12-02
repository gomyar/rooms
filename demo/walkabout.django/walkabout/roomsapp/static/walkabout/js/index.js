

var index = {
    playing_games: [],
    available_games: []
};


index.play_game = function(game_id) {
	window.location = "/rooms/play_game/" + game_id;
};

index.join_game = function(game_id) {
	$.post("/rooms/join_game", {"game_id": game_id}).success(
		function(data){
            index.play_game(game_id);
		});
};

index.create_game = function() {
	$.post("/rooms/create_game", {}).success(
		function(data) {
			$location.reload();
		});
};


$( document ).ready(function() {
    $.get("/rooms/playing_games").success(
        function(data){
            index.playing_games = data;
            turtlegui.reload()
        });
     $.get("/rooms/available_games").success(
        function(data){
            index.available_games = data;
            turtlegui.reload()
       });
    turtlegui.reload()
});
